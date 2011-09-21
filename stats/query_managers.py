from utils import mongo_connection
import mongoengine as mdb
from utils.timezones import Pacific_tzinfo
from datetime import datetime, timedelta
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

        if num_updated < len(ids_to_update):
            for id in ids_to_update:
                if not StatsModel.objects(_id=id):
                    cls.create_stats_model(id, update_params)
    
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
        
def _get_update_params(fields, day, hour):
    #TODO: NEXT TWO LINES FOR TESTING ONLY
    day = 1
    hour = 0
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

                       
    
