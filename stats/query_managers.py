from utils import mongo_connection
import mongoengine as mdb
from utils.timezones import Pacific_tzinfo
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from models import StatsModel, Counts, HourCounts

class StatsModelQueryManager(object):
    _WILD = '*'

    #TODO: replace ensure_connection calls w/ decorator
    @classmethod
    def update_counts(cls,
                      creative_id=None,
                      adgroup_id=None,
                      campaign_id=None,
                      adunit_id=None,
                      app_id=None,
                      fields=None,
                      dt=None):
        mongo_connection.ensure_connection()
        fields = fields or {}
        dt = dt or datetime.now(Pacific_tzinfo())
        
        ids_to_update = _get_ids(dt,
                                 [app_id, adunit_id, cls._WILD],
                                 [creative_id, adgroup_id, campaign_id, cls._WILD])
        
        update_params = _get_update_params(fields, dt.day, dt.hour)
        num_updated = StatsModel.objects(_id__in=ids_to_update).\
            update(**update_params)
        
        #if not updated, means key was not present in mongo. Run through all keys
        #initializing StatsModel for each that is missing
        if num_updated < len(ids_to_update):
            for id in ids_to_update:
                if not StatsModel.objects(_id=id):
                    cls.create_stats_model(id, update_params)
    
    @classmethod
    def get_stats(cls,
                  pub_id='*',
                  adv_id='*',
                  start_date=None,
                  end_date=None):
        """
        pub_id refers to one of the following: App, AdUnit, *
        adv_id refers to one of the following: Campaign, AdGroup, Creative
        """
        start_date = start_date or datetime.now(Pacific_tzinfo()).date()
        end_date = end_date or datetime.now(Pacific_tzinfo()).date()
        results = {"req_count" : {},
                   "imp_count" : {},
                   "click_count" : {},
                   "conv_count" : {},
                   "att_count" : {}
                   }
        for year, month, start_day, end_day \
                in _gen_range(start=start_date,end=end_date):
            cls.get_stats_within_month(pub_id=pub_id,
                                   adv_id=adv_id,
                                   year_month="%s-%02d" % (year, month),
                                   start_day=start_day,
                                   end_day=end_day,
                                   results=results)
        print results
        
    @classmethod
    def get_stats_within_month(cls,
                               pub_id='*',
                               adv_id='*',
                               year_month=None,
                               start_day=None,
                               end_day=None,
                               results=None):
        """
        stub implementation for testing
        """
        mongo_connection.ensure_connection()
        key = StatsModel.get_primary_key(year_month, pub_id, adv_id)
        objs = StatsModel.objects(_id=key)
        if len(objs):
            for count in objs[0].day_counts:
                date_str = "%s-%02d" % (year_month, count.day)
                if date_str in results["req_count"]:
                    results["req_count"][date_str] += count.req_count
                else:
                    results["req_count"][date_str] = count.req_count
        

    @classmethod
    def create_stats_model(cls, id, update_params):
        """
        When creating stats model, initialize empty counts for entire month.
        This will minimize data movement on the mongo end. The document
        will be initialzed once, then simply updated throughout the month.
        """
        day_counts = []
        hour_counts = []
        #TODO: use actual # of days/hour in month
        for day in xrange(1, 4):
            day_counts.append(Counts(day=day))
            for hour in xrange(3):
                hour_counts.append(HourCounts(day=day, hour=hour))
        (dt, pub_id, adv_id) = id.split(":")
        stats_model = StatsModel(dt=dt,
                                 pub_id=pub_id,
                                 adv_id=adv_id,
                                 day_counts=day_counts,
                                 hour_counts=hour_counts)
        #TODO: combine these two steps
        stats_model.save()
        StatsModel.objects(_id=id).update(**update_params)

def _gen_range(start, end):
    """
    Takes in a start and end date
    Generates a list of tuples representing the range of days
    that should be summed for each month. Each tuple is of the form:
      (year, month, start_day, end_day)
    For example, with inputs of start=2011-01-05 and end=2011-03-15, we gen:
    (2011, 1, 5, 31)
    (2011, 2, 1, 31)
    (2011, 3, 1, 15)
    Note: for simplicity, we assume each month has 31 days. This is safe b/c
    the model assumes this as well and initializes counts for all days to be 0
    so this will never cause incorrect count calculations
    """
    while start <= end:
        if (start.year == end.year and start.month == end.month):
            #final month in sequence, end day will be end.day
            yield (start.year, start.month, start.day, end.day)
        else:
            #not final month in sequence, so include until end of month
            yield (start.year, start.month, start.day, 31)
        start = date(start.year, start.month, 1) + relativedelta(months=+1)
        
def _get_update_params(fields, day, hour):
    #TODO: NEXT TWO LINES FOR TESTING ONLY
    day = 1
    hour = 1
    day_index = day-1
    hour_index = 24*(day-1) + hour
    params = {}
    update_param_template = "inc__%s__%s__%s"
    for field, incr in fields.items():
        cur_day_key = update_param_template % ("day_counts", day_index, field)
        cur_hour_key = update_param_template % ("hour_counts", hour_index, field)
        params[cur_day_key] = incr
        params[cur_hour_key] = incr
    return params

def _get_ids(dt, pub_list, adv_list):
    year_month = "%s-%02d" % (dt.year, dt.month)
    return [StatsModel.get_primary_key(year_month,pub, adv) 
            for pub in pub_list
            for adv in adv_list]

                       
    
