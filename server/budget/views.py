from datetime import datetime, timedelta
import time

import urllib2
from urllib import urlencode

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse
from common.utils.timezones import Pacific_tzinfo
# from common.ragendja.auth.decorators import google_login_required as login_required
from advertiser.models import ( Campaign,
                                AdGroup,
                                )
from budget import budget_service
from budget.helpers import get_slice_from_datetime, get_slice_from_ts
from budget.memcache_budget import set_slice
from budget.models import Budget, BudgetSliceCounter

from adserver_constants import (ADSERVER_HOSTNAME,
                                BUDGET_DATA_URL,
                                BUDGET_TS_DATA_URL,
                                BUDGET_DAILY_DATA_URL,)

import logging

# For taskqueue
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp

# The constraints:
# The maximum bucket size is 100
# Each worker must complete in less than a timeslice to avoid contention
CAMPAIGNS_PER_WORKER = 30

DEF_URL = 'http://' + ADSERVER_HOSTNAME
DEF_BUDGET_DATA_URL = DEF_URL + BUDGET_DATA_URL
DEF_BUDGET_TS_DATA_URL = DEF_URL + BUDGET_TS_DATA_URL
DEF_BUDGET_DAILY_DATA_URL = DEF_URL + BUDGET_DAILY_DATA_URL

BUDGET_DAILY_LOG_DATE_FMT = '%Y%m%d'

def budget_advance(request):
    slice_counter = BudgetSliceCounter.all().get()
    # If there is no global counter, then create it
    if not slice_counter:
        logging.warning("%s" % datetime.now())
        slice_counter = BudgetSliceCounter(slice_num = get_slice_from_datetime(datetime.utcnow()))
        # otherwise incr it
    else:
        slice_counter.slice_num = get_slice_from_datetime(datetime.utcnow())

    slice_counter.put()
    # set it memc
    set_slice(slice_counter.slice_num)

    budgets = Budget.all().filter('active =', True).fetch(1000000)
    #campaigns = Campaign.all().filter("budget >", 0).filter("active =", True).fetch(1000000)
    keys = [budget.key() for budget in budgets]
    count = len(keys)

    # Break keys into shards of 30 and send them to a worker
    start_index = 0
    end_index = CAMPAIGNS_PER_WORKER

    text = ''

    while start_index < count:

        key_shard = keys[start_index:end_index]

        # Add the task to the default queue.

        serial_key_shard = ''
        for key in key_shard:
            serial_key_shard += str(key) + ','

        serial_key_shard = serial_key_shard[:-1]
        text += '<br><br> %s:%s has value: %s' % (start_index, end_index, serial_key_shard)

        # serialization of dict objects fails for params so we do it manually
        # key_shard = [str(key) for key in key_shard]

        taskqueue.add(url='/m/budget/advance_worker/',
                      queue_name='budget-advance',
                      params={'key_shard': serial_key_shard}
                      )

        start_index += CAMPAIGNS_PER_WORKER
        end_index += CAMPAIGNS_PER_WORKER

    return HttpResponse('Advanced budget timeslices: %s' % text)

def advance_worker(request, key_shard=None):

    serial_key_shard = key_shard or request.POST['key_shard']
    keys = serial_key_shard.split(',')

    budgets = Budget.get(keys)
    for budg in budgets:
        try:
            budget_service.timeslice_advance(budg, budg.testing)
        except:
            logging.warning("Error advancing budget: %s" % budg)

    return HttpResponse('Worker Succeeded')

def chart(request, campaign_key):
    camp = Campaign.get(campaign_key)

    context =  {'campaign_key': campaign_key,
                'campaign': camp}

    return render_to_response(request,'budget/chart.html', context)



def budget_view(request, adgroup_key):
    adgroup = AdGroup.get(adgroup_key)
    camp = adgroup.campaign

    default_query_dict = dict(key_type='campaign',
                              key=str(camp.key()))


    data_qs = urlencode(default_query_dict)
    data_full_url = DEF_BUDGET_DATA_URL + '?' + data_qs
    logging.warning("Trying for data: %s" % data_full_url)
    remote_data_dict = simplejson.loads(urllib2.urlopen(data_full_url).read())

    if remote_data_dict:
        remaining = remote_data_dict['remaining']
        remaining_daily_budget = remaining['daily_rem']
        remaining_ts_budget = remaining['expected_rem']
        braking_fraction = remote_data_dict['braking_fraction']
        expected = remote_data_dict['expected_spent']
        daily_total = remote_data_dict['spending']['daily_spend']
        total = remote_data_dict['spending']['total_spend']
        slice_budget = remote_data_dict['slice_budget']
    else:
        remaining_ts_budget = None
        remaining_daily_budget = None
        braking_fraction = None
        expected = None
        daily_total = None
        total = None
        slice_budget = None

    ######### Construct TS Log request URL for today's logs ########
    today = datetime.now().date()
    day_start_slice = get_slice_from_datetime(today)

    # Needed for getting TS logs
    now_slice = get_slice_from_datetime(datetime.utcnow())
    count = now_slice - day_start_slice

    ts_query_dict = dict(slice_num=now_slice,
                         count=count)
    ts_query_dict.update(default_query_dict)
    ts_data_qs = urlencode(ts_query_dict)

    ts_full_url = DEF_BUDGET_TS_DATA_URL + '?' + ts_data_qs
    logging.warning("Trying for TS logs: %s" % ts_full_url)
    ts_remote_dict = simplejson.loads(urllib2.urlopen(ts_full_url).read())



    ######### Construct daily log request URL #############
    one_month_ago = today - timedelta(days=30)
    start_date = today.strftime(BUDGET_DAILY_LOG_DATE_FMT)
    end_date = one_month_ago.strftime(BUDGET_DAILY_LOG_DATE_FMT)
    daily_log_query_dict = dict(start_date=start_date,
                                end_date=end_date)
    daily_log_query_dict.update(default_query_dict)
    daily_log_qs = urlencode(daily_log_query_dict)

    daily_log_full_url = DEF_BUDGET_DAILY_DATA_URL + '?' + daily_log_qs
    logging.warning("Trying for daily logs: %s" % daily_log_full_url)

    daily_log_remote_dict = simplejson.loads(urllib2.urlopen(daily_log_full_url).read())

    daily_logs = daily_log_remote_dict['daily_logs']
    ts_logs = ts_remote_dict['ts_logs']

    #daily_logs = budget_service._get_daily_logs_for_date_range(budget,
    #                                                           one_month_ago,
    #                                                           today)
#
#
#    ts_logs = budget_service._get_ts_logs_for_date_range(budget, today, today)

    clear_memcache_ts_url = 'http://www.DONOTFUCKINGCLICKTHIS.com'

    context =  {'campaign': camp,
                'remaining_daily_budget': remaining_daily_budget,
                'remaining_ts_budget': remaining_ts_budget,
                'daily_logs': daily_logs,
                'ts_logs': ts_logs,
                'today': today,
                'one_month_ago': one_month_ago,
                'budget_obj_url': data_full_url,
                'clear_memcache_ts_url': clear_memcache_ts_url,
                'braking_fraction': braking_fraction,
                'expected': expected,
                'total': total,}




    return render_to_response(request,'budget/budget_view.html', context)
