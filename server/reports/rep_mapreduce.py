from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

import logging
import re
import datetime

#GAE imports
from google.appengine.ext import blobstore
from google.appengine.api import mail 
from mapreduce import base_handler
from mapreduce import context 
from mapreduce import mapreduce_pipeline
from mapreduce import operation as op
from mapreduce import shuffler
from mail.mails import REPORT_FINISHED_SIMPLE

#Mopub imports
from reports.models import Report
from common.constants import (APP,
                              AU,
                              CAMP,
                              CRTV,
                              P,
                              MO,
                              WEEK,
                              DAY,
                              HOUR,
                              CO,
                              MAR,
                              BRND,
                              OS,
                              OS_VER,
                              KEY,
                              DATE_FMT,
                              )
from common.utils import date_magic
from common.utils.helpers import parse_time


MR1_KEY = '%s'
MR2_KEY = '%s:%s'
MR3_KEY = '%s:%s:%s'

NO_REQUESTS = (CAMP, CRTV, P)

VIEW_REP_URL = 'http://app.mopub.com/reports/view/%(report_key)s/'

def get_key(line_dict, dim):
    """ Returns the key for a dim

    Args:
        line_dict: parsed log line
        dim: dimension that a key is needed for
    """
    #worry about resolving these when rendering the report, need for speed RIGHT NAO
    if APP == dim:
        return line_dict['adunit']
    if AU == dim:
        return line_dict['adunit']
    if CAMP == dim:
        return line_dict['creative']
    if CRTV == dim:
        return line_dict['creative']
    if P == dim:
        return line_dict['creative']
    if MO == dim:
        return line_dict['time']
    if WEEK == dim: 
        return line_dict['time']
    if DAY == dim:
        return line_dict['time']
    if HOUR == dim:
        return line_dict['time']
    if CO == dim:
        #TODO somehow get the full country name from the 2 letter country code
        return line_dict['country']
    if MAR == dim: 
        return line_dict['marketing_name']
    if BRND == dim:
        return line_dict['brand_name']
    if OS == dim:
        return line_dict['os']
    if OS_VER == dim:
        return line_dict['os_ver']


# k = k:adunit_id:creative_id:country_code:brand_name:marketing_name:device_os:device_os_version:time
# v = [req_count, imp_count, clk_count, conv_count,]# user_count]
def parse_line(line):
    """ Takes a line from the stats Blobfile and turns it into a dictionary where values are
    of the correct type (ie not strings)

    Args:
        line: the line to be parsed
    """
    #Lines have varying amts of whitespace, get rid of all of it
    line = re.sub(r'\s','',line)
    #get the key and value away from each other
    key, value = line.split('[')
    #get rid of the trailing bracket
    value = value.replace(']', '')
    #ph = k, needed a placeholder 
    ph, adunit_id, creative_id, country, brand, marketing, os, os_ver, time = key.split(':')
    
    #just keep one obj here, it's easier
    vals = map(int, value.split(','))

    au = adunit_id
    crtv = creative_id

    #Huzzah
    return dict(adunit = au,
                creative = crtv,
                country = country,
                brand_name = brand,
                marketing_name = marketing,
                os = os,
                os_ver = os_ver,
                time = time,
                vals = vals,
                )


def verify_line(line_dict, d1, d2, d3, days):
    if line_dict is None:
        return False
    return True

def build_keys(line_dict, d1, d2, d3):
    #if we're on a line w/ no creative it's a request line, return what we have
    if line_dict['creative'] == '' and d1 in NO_REQUESTS:
        return None
    d1_key = get_key(line_dict, d1)   
    keys = [MR1_KEY % d1_key]
    if d2:
        if line_dict['creative'] == '' and d2 in NO_REQUESTS:
            return keys
        d2_key = get_key(line_dict, d2)
        keys.append(MR2_KEY % (d1_key, d2_key))
    if d3:
        if line_dict['creative'] == '' and d3 in NO_REQUESTS:
            return keys 
        d3_key = get_key(line_dict, d3)
        keys.append(MR3_KEY % (d1_key, d2_key, d3_key))
    return keys

def generate_report_map(data):
    byte_offset, line = data
    """ Mapping portion of mapreduce job

    Args:
        byte_offset: offset into blob file that line starts on
        line: The value of the line

    """
    ctx = context.get()
    params = ctx.mapreduce_spec.mapper.params
    d1 = params['d1']
    d2 = params['d2']
    d3 = params['d3']
    start = datetime.datetime.strptime(params['start'], DATE_FMT).date()
    end = datetime.datetime.strptime(params['end'], DATE_FMT).date()

    #Turn start, end dates into a list of date_hours
    #reduce turns [[day1hours][day2hours]] into [day1hours, day2hours]
    days = date_magic.gen_days(start, end, True)
    line_dict = parse_line(line)

    #make sure this is the right everything
    if verify_line(line_dict, d1, d2, d3, days):
        for key in build_keys(line_dict, d1, d2, d3):
            yield (key, '%s' % line_dict['vals']) 

def generate_report_reduce(key, values):
    #yield 'key: %s values: %s\n' % (key, [a for a in values])
    values = [eval(value) for value in values]
    #zip turns [1,2,3] [4,5,6] into [(1,4), (2,5), (3,6)], map applies sum to all list entries
    yield '%s||%s\n' % (key, map(sum, zip(*values)))



class GenReportPipeline(base_handler.PipelineBase):
    """ Pipeline for starting a report generation mapreduce job
        
        Args:
            blob_keys: list of blob_keys containing lowest level
                stats objects
            shards: number of shards to run this MR job on
            d*: d* for the report
            start: start date string for this report
            end: end date string for this report
    """
    def run(self, blob_keys, shards, d1, d2, d3, start, end, *args, **kwargs):
        yield mapreduce_pipeline.MapreducePipeline(
                'BlobReportGenerator',
                'reports.rep_mapreduce.generate_report_map',
                'reports.rep_mapreduce.generate_report_reduce',
                'mapreduce.input_readers.BlobstoreLineInputReader',
                'mapreduce.output_writers.BlobstoreOutputWriter',
                mapper_params={
                    'd1': d1,
                    'd2': d2,
                    'd3': d3,
                    'start': start,
                    'end': end,
                    'blob_keys': blob_keys,
                },
                reducer_params={
                    'mime_type': 'text/plain',
                },
                shards=max(shards, 3))

    def finalized(self):
        if not self.was_aborted and self.pipeline_id == self.root_pipeline_id:
            report_key = self.kwargs['report_key']
            user_email = self.kwargs['user_email']
            rep = Report.get(report_key)
            outs = self.outputs.default.value[0]
            for val in outs.split('/'):
                if val == '' or val == 'blobstore':
                    continue
                else:
                    rep.report_blob = blobstore.BlobInfo.get(blobstore.BlobKey(val))
                    rep.put()
            mesg = mail.EmailMessage(sender = 'olp@mopub.com',
                                     subject = 'Your report has completed')
            if user_email:
                # we can do a lot fancier logic here based on people's names and things 
                #this is just a really quick and easy way to get it working though
                mesg_dict = dict(report_key = str(rep.schedule.key()))
                mesg.to = user_email
                mesg.body = REPORT_FINISHED_SIMPLE % mesg_dict
                mesg.send()




