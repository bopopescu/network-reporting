from __future__ import with_statement
from django.conf import settings

import datetime
import logging
import random
import sys
import time
import traceback
import urllib
import urllib2
import uuid

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

# from appengine_django import LoadDjango
# LoadDjango()

from google.appengine.datastore import entity_pb
from google.appengine.ext import db
from google.appengine.api import files
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext.db import BadKeyError
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

from common.utils import helpers
from common.utils import simplejson
from common.utils.timezones import Pacific_tzinfo

from stats import stats_accumulator
from stats import log_service

from reporting import models as r_models
from reporting import query_managers

from account.models import Account
from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import Site as AdUnit, App


############### boto S3 ###############
from boto.s3.connection import S3Connection
from boto.s3.key import Key

S3_CONN = S3Connection('AKIAJKOJXDCZA3VYXP3Q', 'yjMKFo61W0mMYhMgphqa+Lc2WX74+g9fP+FVeyoH')
BUCKET = S3_CONN.get_bucket('mopub-aws-logging')
S3_FILE = Key(BUCKET)
############### boto S3 ###############


OVERFLOW_TASK_QUEUE_NAME_FORMAT = "bulk-log-processor-overflow-%02d"
NUM_OVERFLOW_TASK_QUEUES = 3

MAX_KEYS = 100
MAX_TAIL = 1000 # implies max 100 qps

# soft limit
MAX_PUT_SIZE = 8

STATS_MODEL_QUERY_KEY = "sm"

MDB_STATS_UPDATER_IP = 'http://write.mongostats.mopub.com'
MDB_STATS_UPDATER_HANDLER_PATH = '/stats/update'


# DEREF_CACHE description:
# global dict containing str(key) mappings among publisher and advertiser models:
# {adunit_str: [app_str, account_str],
#  adgroup_str: [campaign_str, account_str],
#  creative_str: [adgroup_str, campaign_str, account_str],
#  account_str: account object}
DEREF_CACHE = {}


def increment_stats(stats):
    # datastore get
    key_name = stats.key()
    stats_obj = Counter.get_by_key(key_name)
    if stats_obj:
        stats_obj += stats
    else:
        stats_obj = stats

    # datastore put
    # logging.info("putting in key_name: %s value: %s,%s"%(key_name,stats.request_count,stats.impression_count))
    # logging.info("putting in key_name: %s NEW value: %s,%s"%(key_name,stats_obj.request_count,stats_obj.impression_count))
    stats_obj.put()

def update_stats(stats_dict,publisher,advertiser,date_hour,country,attribute,req=None,revenue=None,incr=1):
    publisher = publisher or None
    advertiser = advertiser or None
    try:
        key = r_models.StatsModel.get_key_name(publisher=publisher,
                                               advertiser=advertiser,
                                               date_hour=date_hour,
                                               country=country)
        if not key in stats_dict:
            stats_dict[key] = r_models.StatsModel(publisher=publisher,
                                                  advertiser=advertiser,
                                                  date_hour=date_hour,
                                                  country=country)

        if attribute:
            # stats_dict[key].attribute += incr
            setattr(stats_dict[key],attribute,getattr(stats_dict[key],attribute)+incr)

            if revenue:
                stats_dict[key].revenue += revenue
        if req:
            stats_dict[key].reqs.append(req)
    except Exception, e:
        logging.warning("Error in update_stats: %s"%e)


def _create_mdb_json(stats_to_put):
    # format of d:
    # { (adunit, creative, date_hour):
    #   {'attempt_count': int, 'impression_count': int, 'click_count': int, 'conversion_count': int, 'revenue': float}
    # }
    d = {}

    # format of request_d:
    # { (adunit, date_hour): request_count }
    request_d = {}  # no creative

    for s in stats_to_put:
        key_name = s.key().name()

        if key_name.endswith('offline'):
            logging.error('Error in parsing StatsModel keyname %s -- should not be offline' %key_name)
            continue

        parts = key_name.split(':')

        # remove country
        adunit = parts[1]
        creative = parts[2]
        date_hour = parts[-1]   # for real-time StatsModels, the date section should always be last!

        if not creative:    # REQUEST: /m/ad
            request_d[(adunit, date_hour)] = request_d.get((adunit, date_hour), 0) + s.request_count
        else:               # ATTEMPT: /m/req
            counts = {}
            counts['attempt_count'] = s.request_count
            counts['impression_count'] = s.impression_count
            counts['click_count'] = s.click_count
            counts['conversion_count'] = s.conversion_count
            counts['revenue'] = s.revenue

            key_tuple = (adunit, creative, date_hour)

            # roll up stat counts across all countries
            if key_tuple in d:
                # sum up the 2 arrays if key already exists
                d[key_tuple]['attempt_count'] += counts['attempt_count']
                d[key_tuple]['impression_count'] += counts['impression_count']
                d[key_tuple]['click_count'] += counts['click_count']
                d[key_tuple]['conversion_count'] += counts['conversion_count']
                d[key_tuple]['revenue'] += counts['revenue']
            else:
                d[key_tuple] = counts


    # create new dict json_d with string keys (for json serialization)
    # combination of d and request_d dicts
    # format of json_d:
    # { 'adunit:creative:date_hour':
    #   {'request_count': int, 'attempt_count': int, 'impression_count': int, 'click_count': int, 'conversion_count': int, 'revenue': float}
    # }
    json_d = {}
    for (adunit, creative, date_hour), counts in d.iteritems():
        k = '%s:%s:%s' % (adunit, creative, date_hour)
        json_d[k] = d[(adunit, creative, date_hour)]
        json_d[k]['request_count'] = 0

    # these are request counts only; insert them into json_d
    for (adunit, date_hour), req_count in request_d.iteritems():
        k = '%s::%s' % (adunit, date_hour)
        counts = {}
        counts['request_count'] = req_count
        # all other counts are 0
        counts['attempt_count'] = 0
        counts['impression_count'] = 0
        counts['click_count'] = 0
        counts['conversion_count'] = 0
        counts['revenue'] = 0
        json_d[k] = counts

    return simplejson.dumps(json_d)


# takes in dict form of mdb_json from _create_mdb_json
# returns error flag, error msg (if error flag is True), and list of dicts of derefed data in string json form (if error flag is False)
def _package_mdb_post_data(mdb_dict):
    mdb_post_list = []

    # key format -> adunit:creative:date_hour
    # value format -> {'request_count':int, 'attempt_count':int, 'impression_count':int, 'click_count':int, 'conversion_count':int, 'revenue':float}
    for k, v in mdb_dict.iteritems():
        parts = k.split(':')
        if len(parts) != 3:
            err_msg = 'Error parsing %s -- expecting format adunit:creative:date_hour' % k
            return True, err_msg, None

        [adunit, creative, date_hour] = parts

        # NOTE: deref adunit after creative, since there's a bug where the account is not guaranteed to be retrieved from creative
        # if creative is empty string, the creative field in the post_dict will just be emptry string while adgroup and campaign
        # will be None
        [adgroup, campaign, account] = _deref_creative(creative) or [None, None, None]
        [app, account] = _deref_adunit(adunit) or [None, None]


        if None not in [app, account]:
            post_dict = {'adunit': adunit,
                         'app': app,
                         'account': account,
                         'creative': creative,
                         'adgroup': adgroup,
                         'campaign': campaign,
                         'date_hour': date_hour,
                         'request_count': v['request_count'],
                         'attempt_count': v['attempt_count'],
                         'impression_count': v['impression_count'],
                         'click_count': v['click_count'],
                         'conversion_count': v['conversion_count'],
                         'revenue': v['revenue']}
            mdb_post_list.append(post_dict)
        else:
            err_msg = 'None derefed for key_tuple %s: app=%s, account=%s, adgroup=%s, campaign=%s' % (k, app, account, adgroup, campaign)
            return True, err_msg, None

    # post the list of dicts to MongoDB
    post_data = simplejson.dumps(mdb_post_list)
    return False, None, post_data


# returns [app_str, account_str] or None
def _deref_adunit(adunit_str):
    if adunit_str in DEREF_CACHE:
        return DEREF_CACHE[adunit_str]

    try:
        adunit_key = db.Key(adunit_str)
        adunit = AdUnit.get(adunit_key)
        app_str = str(adunit._app_key)
        account_str = str(adunit._account)
        DEREF_CACHE[adunit_str] = [app_str, account_str]
        return [app_str, account_str]
    except BadKeyError, e:
        logging.error('deref BadKeyError on adunit %s: %s' %(adunit_str, e))
        return None
    except Exception, e:
        logging.error('deref error on adunit %s: %s' %(adunit_str, e))
        return None


# returns [campaign_str, account_str] or None
def deref_adgroup(adgroup_str):
    if adgroup_str in DEREF_CACHE:
        return DEREF_CACHE[adgroup_str]

    try:
        adgroup_key = db.Key(adgroup_str)
        adgroup = AdGroup.get(adgroup_key)
        campaign_str = str(adgroup._campaign)
        account_str = str(adgroup._account)
        DEREF_CACHE[adgroup_str] = [campaign_str, account_str]
        return [campaign_str, account_str]
    except BadKeyError, e:
        logging.error('deref BadKeyError on adgroup %s: %s' %(adgroup_str, e))
        return None
    except Exception, e:
        logging.error('deref error on adgroup %s: %s' %(adgroup_str, e))
        return None


# returns [adgroup_str, campaign_str, account_str] or None
def _deref_creative(creative_str):
    if not creative_str:    # None or ''
        return None

    if creative_str in DEREF_CACHE:
        return DEREF_CACHE[creative_str]

    try:
        creative_key = db.Key(creative_str)
        creative = Creative.get(creative_key)
        adgroup_str = str(creative._ad_group)
        adgroup_deref_results = deref_adgroup(adgroup_str)
        if adgroup_deref_results:
            [campaign_str, account_str] = adgroup_deref_results
            DEREF_CACHE[creative_str] = [adgroup_str, campaign_str, account_str]
            return [adgroup_str, campaign_str, account_str]
    except BadKeyError, e:
        logging.error('deref BadKeyError on creative %s: %s' %(creative_str, e))
        return None
    except Exception, e:
        logging.error('deref error on creative %s: %s' %(creative_str, e))
        return None


class LogTaskHandler(webapp.RequestHandler):
  def get(self):
      # inspect headers of the task
      retry_count = int(self.request.headers.get('X-AppEngine-TaskRetryCount',"0"))

      if retry_count > 6: return # bail early


      task_name = self.request.headers.get('X-AppEngine-TaskName',None)
      queue_name = self.request.headers.get('X-AppEngine-QueueName',None)

      memcache_stats_start = memcache.get_stats()
      memcache_stats = None
      # grab parameters from the message of the task
      account_name = self.request.get("account_name")
      account_shard = self.request.get("account_shard")
      time_bucket = int(self.request.get("time"))


      head_index = 1 # starts at one for a particular time_bucket

      # get the last index for a given time bucket

      # for a brief moment there will be tasks that were put in without an associated shard
      if account_shard is None or account_shard == '':
          tail_key = stats_accumulator.INDEX_KEY_FORMAT_OLD%dict(account_name=account_name,time=time_bucket)
      else:
          tail_key = stats_accumulator.INDEX_KEY_FORMAT%dict(account_name=account_name,
                                                      account_shard=int(account_shard),
                                                      time=time_bucket)
      tail_index_str = memcache.get(tail_key)
      if not tail_index_str:
          memcache_stats = memcache_stats or memcache.get_stats()
      tail_index = int(tail_index_str or MAX_TAIL)


      # if account_name == "agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww":
      #     logging.error("account: %s time: %s start: %s stop: %s"%(account_name,time_bucket,head_index,tail_index))
      #     logging.error("MEMCACHE STATS: %s"%memcache_stats_start)
      # else:
      #     logging.info("account: %s time: %s start: %s stop: %s"%(account_name,time_bucket,head_index,tail_index))
      #     logging.info("MEMCACHE STATS: %s"%memcache_stats_start)


      stats_dict = {}
      start = head_index
      # paginate the keys
      memcache_misses = 0

      while start <= tail_index:
          # get another MAX_KEYS or go to the end
          stop = start + MAX_KEYS - 1 if (start+MAX_KEYS-1) < tail_index else tail_index

          # if this is an old task we don't use the shard to make the keys
          if account_shard is None or account_shard == '':
              keys = [stats_accumulator.LOG_KEY_FORMAT_OLD%dict(account_name=account_name,time=time_bucket,log_index=i)
                       for i in range(start,stop+1)]
          else:
              keys = [stats_accumulator.LOG_KEY_FORMAT%dict(account_name=account_name,account_shard=int(account_shard),time=time_bucket,log_index=i)
                       for i in range(start,stop+1)]

          # logging.info("we have %d keys (start:%s stop:%s)"%(len(keys),start,stop))

          # grab logs from memcache
          data_dicts = memcache.get_multi(keys)
          current_memcache_misses = (stop - start+1) - len(data_dicts)
          memcache_misses += current_memcache_misses
          if memcache_misses:
              memcache_stats = memcache_stats or memcache.get_stats()
          # logging.info("Memcache misses: %d"%current_memcache_misses)

          for k,d in data_dicts.iteritems():
              if d:
                  uid = d.get('udid',None)
                  adunit = d.get('adunit',None)
                  creative = d.get('creative',None)
                  event = d.get('event',None)

                  req = d.get('req',None)
                  req = int(req) if req else None

                  revenue = d.get('revenue',None)
                  revenue = float(revenue) if revenue else None

                  inst = d.get('inst',None)
                  inst = int(inst) if inst else None

                  req = "%s.%s.%s"%(req,inst,time_bucket)

                  appid = d.get('appid',None)

                  country = d.get('country',None)

                  # calculate the datetime object to hour precision
                  now = int(float(d['now']))
                  hour = now-now%3600
                  date_hour = datetime.datetime.fromtimestamp(hour,
                                                              tz=r_models.Pacific_tzinfo())
                  # attach on the request id once per log line
                  # update_stats(stats_dict,
                  #              publisher=adunit,
                  #              advertiser=None,
                  #              date_hour=date_hour,
                  #              attribute=None,
                  #              req=req)

                  if event == stats_accumulator.REQ_EVENT:
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,
                                   attribute='request_count')
                  elif event == stats_accumulator.IMP_EVENT:
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,
                                   attribute='impression_count',
                                   revenue=revenue)

                  if event == stats_accumulator.CLK_EVENT:
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,
                                   attribute='click_count',
                                   revenue=revenue)

                  elif event == stats_accumulator.CONV_EVENT:
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,
                                   attribute='conversion_count',
                                   revenue=revenue)

              else:
                  logging.error("NO value for key %s exists"%k)

          start += MAX_KEYS # proceed to the next "page"

      query_manager = query_managers.StatsModelQueryManager(account_name)

      try:
          # stats_dict structure:
          # key is StatsModel key_name
          # value is StatsModel object
          stats_to_put = stats_dict.values()

          # if account_name == "agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww":
          #     try:
          #         mail.send_mail_to_admins(sender="olp@mopub.com",
          #                                  subject="WTF",
          #                                  body="len: %s\n%s"%(len(stats_to_put),
          #                                       [(str(s._advertiser), str(s._publisher), s.country, s.impression_count) for s in stats_to_put if str(s.country) == 'US']))
          #     except Exception, e:
          #         logging.error("MAIL ERROR: %s",e)

          # retrieve account object from cache if possible
          if account_name in DEREF_CACHE:
              account = DEREF_CACHE[account_name]
          else:
              account = Account.get(account_name)
              DEREF_CACHE[account_name] = account

          # post to MDB servers if account is using MongoDB for realtime stats
          if account and account.use_mongodb_stats:
              mdb_json = _create_mdb_json(stats_to_put)
              try:
                  taskqueue.add(name='mdb-'+task_name,
                                queue_name=queue_name.replace('bulk-log-processor','mongo-rt-stats'),
                                method='post',
                                url='/mdb/update_stats',
                                countdown=random.uniform(0,9), # splay out the requests so as not be so spikey
                                payload=mdb_json)
              except taskqueue.TaskAlreadyExistsError:
                  logging.info('task %s already exists' % ('mdb-'+task_name))
              if account.use_only_mongo:
                  return    # don't move on to traditional realtime stats put below

          if settings.DEBUG:
              # traditional put to GAE datastore
              query_manager.put_stats(stats_to_put)
          # total_stats = query_manager.all_stats_deltas

      # if the transaction is too large then we split it up and try again
      # except db.BadRequestError:
      #     async_put_models(account_name,stats_dict.values(),MAX_PUT_SIZE)

      except:
          if retry_count > 5:
              exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
              base_number_of_stats = len(stats_dict.values())
              total_stats = query_manager.all_stats_deltas
              number_of_stats = len(total_stats)
              max_countries = max([len(stat.get_countries()) for stat in total_stats])
              # account = Account.get(account_name)
              if account:
                  user_email = account.mpuser.email
              else:
                  user_email = None

              try:
                  pass
                  # mail.send_mail_to_admins(sender="olp@mopub.com",
                  #                           subject="Logging error",
                  #                           body="account: %s email: %s retries: %s task name: %s queue name: %s base stats: %s total number of stats: %s max countries: %s \n\n%s"%(account_name,
                  #                                                                                user_email,
                  #                                                                                retry_count,
                  #                                                                                task_name,
                  #                                                                                queue_name,
                  #                                                                                base_number_of_stats,
                  #                                                                                number_of_stats,
                  #                                                                                max_countries,
                  #                                                                                exception_traceback))
              except:
                  pass
              logging.error(exception_traceback)
          raise Exception("need to try transaction again")

      # only email if we miss alot (more than .1% or more than 1)
      if not tail_index_str or (memcache_misses > 1 and float(memcache_misses)/float(tail_index) > 0.01):
          account = Account.get(account_name)
          if account:
              user_email = account.mpuser.email
          else:
              user_email = None

          message = "Account: %s email: %s time: %s tail: %s misses: %s retry: %s\nmemcache_stats_starts:%s\nmemcache_stats:%s"%(account_name,
                                                                                  user_email,
                                                                                  time_bucket,
                                                                                  tail_index_str,memcache_misses,retry_count,
                                                                                  memcache_stats_start,memcache_stats)

          try:
              pass
              # mail.send_mail_to_admins(sender="olp@mopub.com",
              #                           subject="Logging error (cache miss)",
              #                           body=message)
          except:
              pass
          # logging.error(message)

class StatsModelPutTaskHandler(webapp.RequestHandler):
    def get(self):
        # logging.info("ASDF: %s"%"ASdf")
        return self.post()

    def post(self):
        # get the account name
        account_name = self.request.get("account_name")
        next_bucket_size = self.request.get("next_size", MAX_PUT_SIZE)
        query_manager = query_managers.StatsModelQueryManager(account_name)

        # get the list of protobufs from the post
        # stats_model_protobufs = self.request.get_all(STATS_MODEL_QUERY_KEY)
        stats_model_json_strings = self.request.get_all(STATS_MODEL_QUERY_KEY)
        # decode the objects
        # logging.info("length: %s"%len(stats_model_protobufs))
        # logging.info("try: %s"%stats_model_protobufs[0])

        # stats_models = [db.model_from_protobuf(entity_pb.EntityProto(pb))
        #                         for pb in stats_model_protobufs]
        stats_models = [r_models.StatsModel.from_json(jstr) for jstr in stats_model_json_strings]
        try:
            # logging.info('trying to put %d models'%len(stats_models))
            query_manager.put_stats(stats_models)
        # if the transaction is too large then we split it up and try again
        except db.BadRequestError:
            async_put_models(account_name,stats_models,next_bucket_size)

def async_put_models(account_name,stats_models,bucket_size):
    account_bucket = hash(account_name)%NUM_OVERFLOW_TASK_QUEUES
    task_queue_name = OVERFLOW_TASK_QUEUE_NAME_FORMAT%account_bucket
    # logging.info('queue: %s'%task_queue_name)

    next_bucket_size = bucket_size/2 if bucket_size > 1 else 1

    # run in transaction so we atomically "put" all the data chunks
    # logging.info('splitting %d models into %d sized chunks'%(len(stats_models),bucket_size))

    def _txn():
        for sub_stats in helpers.chunks(stats_models, bucket_size):
            # add sub_stats to the key
            stats_model_json_strings = [sm.to_json() for sm in sub_stats]

            t = taskqueue.Task(params={'account_name': account_name,
                                       'next_size': next_bucket_size,
                                       STATS_MODEL_QUERY_KEY: stats_model_json_strings,
                                       },
                               url='/_ah/queue/bulk-log-processor/put',
                               method='POST',
                               countdown=5)
            t.add(task_queue_name, transactional=False)
    db.run_in_transaction(_txn)

class FinalizeHandler(webapp.RequestHandler):
    def post(self):
        post_data = simplejson.loads(self.request.body)
        blob_file_name = post_data['blob_file_name']
        log_lines = post_data['log_lines']  # all log lines are unicode due to simplejson.dumps()

        # write() of files API only uses ascii encoding, which could fail
        # therefore explicitly convert all unicode to string using utf-8 encoding
        ascii_log_lines = [helpers.to_ascii(line) for line in log_lines]

        # create new file in blobstore (file name is GAE internal)
        internal_file_name = files.blobstore.create(
                            mime_type="text/plain",
                            _blobinfo_uploaded_filename=blob_file_name+'.log')

        # open the file and write lines
        with files.open(internal_file_name, 'a') as f:
            f.write('\n'.join(ascii_log_lines)+'\n')

        # finalize this file
        files.finalize(internal_file_name)

        # # posting to S3 directly instead of writing to blobstore (commented out above)
        # now_PST = datetime.datetime.now(Pacific_tzinfo())
        # short_timestamp = now_PST.strftime('%Y-%m%d')
        # long_timestamp = now_PST.strftime('%Y-%m%d-%H%M')
        # s3_filename = '%s_%s.log' % (long_timestamp, str(uuid.uuid4()))
        # s3_path = '/tmp5/logs-%s-full/aws-logfile-%s-0000-full.raw/%s' % (short_timestamp, short_timestamp, s3_filename)
        # S3_FILE.key = s3_path

        # file_content = '\n'.join(ascii_log_lines)+'\n'
        # S3_FILE.set_contents_from_string(file_content)


    def get(self):
        try:
            file_name = self.request.get('file_name')
            files.finalize(file_name)
        except (files.ExistenceError, files.FinalizationError):
            pass # no-opp file is already finalized


class DownloadLogsHandler(webapp.RequestHandler):
    def post(self):
        return self.get(self)

    def get(self, LIMIT=100):
        date_hour_string = self.request.get('dh')
        limit = int(self.request.get('limit', LIMIT))
        start_time_stamp = self.request.get('start_time', None)
        start_key = self.request.get('start_key', None)
        filename = self.request.get('filename', 'apache')

        # date_hour_string = YYYYMMDDHH
        year = int(date_hour_string[:4])
        month = int(date_hour_string[4:6])
        day = int(date_hour_string[6:8])
        hour = int(date_hour_string[8:10])

        date_hour = datetime.datetime(year=year,
                                      month=month,
                                      day=day,
                                      hour=hour)

        filename = log_service.get_blob_name_for_time(date_hour, filename) + '.log'
        blob_infos = BlobInfo.all().filter('filename =',filename)
        if start_time_stamp:
            start_time = datetime.datetime.fromtimestamp(float(start_time_stamp))
            blob_infos = blob_infos.filter('creation >=', start_time).order('creation')

        if start_key:
            blob_infos = blob_infos.filter('__key__ >=', db.Key(start_key))


        # fetch the objects from DB
        blob_infos = blob_infos.fetch(limit+1)

        blob_keys = [bi.key() for bi in blob_infos]

        # if there are limit + 1 entries returned
        # notify the API user where to start next
        if len(blob_infos) > limit:
            next_creation_time_stamp = time.mktime(blob_infos[-1].creation.timetuple())
            next_key_name = blob_infos[-1].key()
        else:
            next_creation_time_stamp = None
            next_key_name = None

        response_dict = dict(urls=['/files/serve/%s'%urllib.quote(str(bk)) for bk in blob_keys[:limit]])
        if next_creation_time_stamp:
            response_dict.update(start_time=str(next_creation_time_stamp))
        if next_key_name:
            # makes pseudo BlobInfo key
            # next_key is actually a BlobKey which is the key_name for the BlobInfo
            next_key = db.Key.from_path(BlobInfo.kind(), str(next_key_name), namespace='')
            response_dict.update(start_key=str(next_key))

        self.response.out.write(simplejson.dumps(response_dict))

class ServeLogHandler(blobstore_handlers.BlobstoreDownloadHandler):
    """Actually serves the file"""
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = BlobInfo.get(resource)
        self.send_blob(blob_info)


class MongoUpdateStatsHandler(webapp.RequestHandler):
    def post(self):
        mdb_dict = simplejson.loads(self.request.body)  # mdb_dict is json_d in _create_mdb_json()

        has_err, err_msg, post_data = _package_mdb_post_data(mdb_dict)
        if has_err:
            logging.error(err_msg)
            #respond immediately without posting any data to MongoDB
            self.response.out.write(err_msg)
            return

        post_url = MDB_STATS_UPDATER_IP + MDB_STATS_UPDATER_HANDLER_PATH # ex: http://write.mongostats.mopub.com/update
        post_request = urllib2.Request(post_url, post_data)
        post_response = urllib2.urlopen(post_request)
        status_code = post_response.code
        response_msg = post_response.read()

        handler_response = '%i response from %s: %s\npayload:\n%s' % (status_code, post_url, response_msg, post_data)
        if status_code == 200: # OK
            logging.info(handler_response)
        else:   # failed
            logging.error(handler_response)
            raise Exception(handler_response)
        self.response.out.write(handler_response)



application = webapp.WSGIApplication([('/_ah/queue/bulk-log-processor', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-00', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-01', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-02', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-03', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-04', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-05', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-06', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-07', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-08', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-09', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor/put', StatsModelPutTaskHandler),
                                      ('/files/finalize', FinalizeHandler),
                                      ('/files/download', DownloadLogsHandler),
                                      ('/files/serve/([^/]+)?', ServeLogHandler),
                                      ('/mdb/update_stats', MongoUpdateStatsHandler),
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
