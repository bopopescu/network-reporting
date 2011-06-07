from mapreduce import operation as op
from mapreduce import context 
from mapreduce import base_handler
from mapreduce import mapreduce_pipeline
from mapreduce import shuffler
from reporting.models import StatsModel
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
from common.utils import date_magic
                            



MR1_KEY = '%s'
MR2_KEY = '%s:%s'
MR3_KEY = '%s:%s:%s'

def get_key(model, dim):
    '''Given a model and a dimension, return the name that this model
    has for that dimension'''
    wurfl_man = WurflQueryManager()
    if APP == dim:
        return model.publisher.app_key.name
    if AU == dim:
        return model.publisher.name
    if CAMP == dim:
        return model.advertiser.adgroup.campaign.name
    if CRTV == dim:
        return model.advertiser.name
    if P == dim:
        return model.advertiser.adgroup.campaign.campaign_type
    if MO == dim:
        return date_magic.date_name(model.date_hour, MO)
    if WEEK == dim: 
        return date_magic.date_name(model.date_hour, WEEK)
    if DAY == dim:
        return date_magic.date_name(model.date_hour, DAY)
    if HOUR == dim:
        return date_magic.date_name(model.date_hour, HOUR)
    if CO == dim:
        #TODO somehow get the full country name from the 2 letter country code
        return model.country
    if MAR == dim: 
        return wurfl_man.get_market_name(model.marketing_name)
    if BRND == dim:
        return wurfl_man.get_brand_name(model.brand_name)
    if OS == dim:
        return wurfl_man.get_os_name(model.device_os)
    if OS_VER == dim:
        return wurfl_man.get_osver_name(model.device_os_version)


#the only models that get to build_keys have only date_hours, 
#pubs are all adunits, and advs are all creatives
def build_keys(model, d1, d2, d3):
    d1_key = get_key(model, d1)
    keys = [MR1_KEY % d1_key]
    if d2:
        d2_key = get_key(model, d2)
        keys.append(MR2_KEY % (d1_key, d2_key))
    if d3:
        d3_key = get_key(model, d3)
        keys.append(MR3_KEY % (d1_key, d2_key, d3_key))
    return keys
    
#Days are always going to be date_hours

#Dont worry about values
#Always make sure pub is adunit, adv is creative
def verify_stat(model, d1, d2, d3, days, account):
    #Verify model is of the correct account
    if model.account != account:
        return False
    #And the SM is in the correct day range
    if model.date_hour not in days:
        return False
    #TODO Check for stupid adunit//app thing because requests are stupid
    if model.is_rollup:
        return False
    #don't have to verify values, just have to properly key them
    return True


def map_rep_gen(stats_model):
    ctx = context.get()
    params = ctx.mapreduce_spec.mapper.params
    d1 = params['d1']
    d2 = d3 = None
    if params['d2'] is not None:
        d2 = params['d2']
    if params['d3'] is not None:
        d3 = params['d3']
    days = params['days']
    acct = params['account']
    if verify_stat(stats_model, d1, d2, d3, days, account):
        for key in build_keys(stats_model, d1, d2, d3):
            yield (key, [stats_model.request_count, stats_model.impression_count, stats_model.click_count, stats_model.conversoin_count]) 

def reduce_rep_gen(key, values):
    #zip each pair of values [1,2,3], [5,6,7] becomes [(1,5), (2,6), (3,7)]
    #sum each pair, and then store them in a list
    yield  "%s| %s" % (key, reduce(lambda x,y: [sum(a) for a in zip(x,y)], values))


#d1 - d3 are 'dim name'
#days is all date_hours
#account needs to be actual account
class ReportMRPipeline(base_handler.PipelineBase):
    #run with REPORT not SCHED_REPORT because run report (how a new report is generated for an old sched_report) only updates the start/end for the report, not the sched_report explicitly
    def run(self, report):
        d1 = report.d1
        d2 = report.d2
        d3 = report.d3
        account = report.account
        #Turn start, end dates into a list of date_hours
        #reduce turns [[day1hours][day2hours]] into [day1hours, day2hours]
        days = reduce(lambda x,y: x+y, date_magic.gen_days(report.start, report.end, True))
        yield mapreduce_pipeline.MapreducePipeline(
                'ReportGenerator',
                'reports.mapreduce.map_rep_gen',
                'reports.mapreduce.reduce_rep_gen',
                'mapreduce.input_readers.DatastoreInputReader',
                'mapreduce.output_writers.BlobstoreOutputWriter',
                mapper_params={
                'account': account,
                'days': days,
                'd1': d1,
                'd2': d2,
                'd3': d3,
                },
                shards=15)
