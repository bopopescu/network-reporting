from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

import logging
import re

#GAE imports
from mapreduce import base_handler
from mapreduce import context 
from mapreduce import mapreduce_pipeline
from mapreduce import operation as op
from mapreduce import shuffler

#Mopub imports
from account.models import Account
from advertiser.models import Campaign, Creative, AdGroup
from publisher.models import App, AdUnit
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
                              )
from common.wurfl.query_managers import WurflQueryManager
from common.utils import date_magic
from common.utils.helpers import parse_time


MR1_KEY = '%s'
MR2_KEY = '%s:%s'
MR3_KEY = '%s:%s:%s'

def get_key(line_dict, dim):
    """ Returns the key for a dim

    Args:
        line_dict: parsed log line
        dim: dimension that a key is needed for
    """
    wurfl_man = WurflQueryManager()
    if APP == dim:
        return line_dict['adunit'].app_key.name
    if AU == dim:
        return line_dict['adunit'].name
    if CAMP == dim:
        return line_dict['creative'].adgroup.campaign.name
    if CRTV == dim:
        return line_dict['creative'].name
    if P == dim:
        return line_dict['creative'].adgroup.campaign.campaign_type
    if MO == dim:
        return date_magic.date_name(line_dict['time'], MO)
    if WEEK == dim: 
        return date_magic.date_name(line_dict['time'], WEEK)
    if DAY == dim:
        return date_magic.date_name(line_dict['time'], DAY)
    if HOUR == dim:
        return date_magic.date_name(line_dict['time'], HOUR)
    if CO == dim:
        #TODO somehow get the full country name from the 2 letter country code
        return line_dict['country']
    if MAR == dim: 
        return wurfl_man.get_market_name(line_dict['marketing_name'])
    if BRND == dim:
        return wurfl_man.get_brand_name(line_dict['brand_name'])
    if OS == dim:
        return wurfl_man.get_os_name(line_dict['os'])
    if OS_VER == dim:
        return wurfl_man.get_osver_name(line_dict['os_ver'])


# k = k:adunit_id:creative_id:country_code:brand_name:marketing_name:device_os:device_os_version:time
# v = [req_count, imp_count, clk_count, conv_count,]# user_count]
def parse_line(line):
    """ Takes a line from the stats Blobfile and turns it into a dictionary where values are
    of the correct type (ie not strings)

    Args:
        line: the line to be parsed
    """
    #Lines have varying amts of whitespace, get rid of all of it
    re.sub(r'\s','',line)
    #get the key and value away from each other
    key, value = line.split('[')
    #get rid of the trailing bracket
    value = value.replace(']', '')
    #ph = k, needed a placeholder 
    ph, adunit_id, creative_id, country, brand, marketing, os, os_ver, time = key.split(':')
    time = parse_time(time)
    req, imp, clk, conv = map(int, value.split(','))
    au = AdUnit.get(adunit_id)
    crtv = Creative.get(creative_id)
    #Huzzah
    return dict(adunit = au,
                creative = crtv,
                country = country,
                brand_name = brand,
                marketing_name = marketing,
                os = os,
                os_ver = os_ver,
                time = time,
                req_count = req,
                imp_count = imp,
                clk_count = clk,
                conv_count = conv,
                )


def verify_line(line_dict, d1, d2, d3, days, account_key):
    if str(creative.account.key()) != account_key:
        return False
    if line_dict['time'] not in days:
        return False
    #Eventually, do things with d1, d2, d3 to do something with checking if no creative
    return True

def build_keys(line_dict, d1, d2, d3):
    d1_key = get_key(line_dict, d1)   
    keys = [MR1_KEY % d1_key]
    if d2:
        d2_key = get_key(line_dict, d2)
        keys.append(MR2_KEY % (d1_key, d2_key))
    if d3:
        d3_key = get_key(line_dict, d3)
        keys.append(MR3_KEY % (d1_key, d2_key, d3_key))
    return keys

def generate_report_map(byte_offset, line):
    """ Mapping portion of mapreduce job

    Args:
        byte_offset: I have no idea what this is for but I get it from MR
        line: The value of the line

    """
    ctx = context.get()
    params = ctx.mapreduce_spec.mapper.params
    report_key = params['report_key']
    report = Report.get(report_key)
    d1 = report.d1
    d2 = report.d2
    d3 = report.d3
    account_key = str(report.account.key())
    #Turn start, end dates into a list of date_hours
    #reduce turns [[day1hours][day2hours]] into [day1hours, day2hours]
    days = reduce(lambda x,y: x+y, date_magic.gen_days(report.start, report.end, True))
    line_dict = parse_line(line)
    #make sure this is the right everything
    if verify_line(line_dict, d1, d2, d3, days, account_key):
        for key in build_keys(line_dict, d1, d2, d3):
            yield (key, [line_dict['req_count'], line_dict['imp_count'], line_dict['clk_count'], line_dict['conv_count']]) 

def generate_report_reduce(key, values):
    #zip turns [1,2,3] [4,5,6] into [(1,4), (2,5), (3,6)], map applies sum to all list entries
    yield '%s|| %s' % (key, reduce(lambda x,y: map(sum, zip(x,y)), values))



class GenReportPipeline(base_handler.PipelineBase):
    """ Pipeline for starting a report generation mapreduce job
        
        Args:
            blob_keys: list of blob_keys containing lowest level
                stats objects
            report_key: key of the report being generated (not scheduled report)
    """
    def run(self, blob_keys, report_key):
        yield mapreduce_pipeline.MapreducePipeline(
                'BlobReportGenerator',
                'reports.rep_mapreduce.generate_report_map',
                'reports.rep_mapreduce.generate_report_reduce',
                'mapreduce.input_readers.BlobstoreLineInputReader',
                'mapreduce.output_writers.BlobstoreOutputWriter',
                mapper_params={
                    'report_key': report_key,
                    'blob_keys': blob_keys,
                },
                reducer_params={
                    'mime_type': 'text/plain',
                },
                shards=25)

