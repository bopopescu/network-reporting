from utils.decorators import requires_mongo
import mongoengine as mdb
from utils.timezones import Pacific_tzinfo
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from models import StatsModel, Counts
from calendar import monthrange

class StatsModelQueryManager(object):
    _WILD = '*'

    """
    used to keep track of which count fields are currently being used.
    in the StatsModel. Whenever StatsModel is updated, be sure and 
    update this dictionary to reflect the change
    """ 
    _count_fields = {'revenue' : 'rev',
                     'request_count' : 'req',
                     'impression_count': 'imp',
                     'click_count' : 'click',
                     'conversion_count' : 'conv',
                     'attempt_count' :'att'}

    
    @classmethod
    @requires_mongo
    def update_counts(cls,
                      creative_id=None,
                      adgroup_id=None,
                      campaign_id=None,
                      adunit_id=None,
                      app_id=None,
                      fields=None,
                      date_hour=None):
        """
        Updates counts in mongo based on passed in parameters. If an item 
        is not present, it is created/stored in mongo
        """
        fields = fields or {}
        date_hour = date_hour or datetime.now(Pacific_tzinfo())
        
        ids_to_update = _get_ids(date_hour, 
                                 [app_id, adunit_id, cls._WILD],
                                 [creative_id, adgroup_id, campaign_id, cls._WILD])
        
        update_params = cls.get_update_params(fields, 
                                              date_hour.day, 
                                              date_hour.hour)
        num_updated = StatsModel.objects(_id__in=ids_to_update).\
            update(**update_params)
        
        # create/store objects for all keys that were not present
        if num_updated < len(ids_to_update):
            for id in ids_to_update:
                if not StatsModel.objects.with_id(id):
                    cls.create_stats_model(id, update_params)
    
    @classmethod
    def get_counts(cls,
                  pub_id='*',
                  adv_id='*',
                  start_date=None,
                  end_date=None):
        """
        pub_id refers to one of the following: App, AdUnit, *
        adv_id refers to one of the following: Campaign, AdGroup, Creative, *

        Returns stats for the given pub_id, adv_id and date range
        Return Values:
        daily_stats:
          [{"field_1" : val, ... , "field_n" : val, "date" : date} , ... 
          {"field_1" : val_m, ... , "field_n" : val_m, "date" : date_m}]
          where field_x corresponds to cls._count_fields keys
          
        sum:
          {"field_1" : sum , ... , "field_n' : sum}
          where sum is the sum over all elements in daily_stats for the 
          given field
        """
        start_date = start_date or datetime.now(Pacific_tzinfo()).date()
        end_date = end_date or datetime.now(Pacific_tzinfo()).date()
        daily_stats = []
        sum = dict([(k,0) for k in cls._count_fields.keys()])
        for year, month, start_day, end_day \
                in _gen_range(start=start_date,end=end_date):
            cls.get_daily_counts_single_month(pub_id=pub_id,
                                              adv_id=adv_id,
                                              year_month="%s-%02d" % (year, month),
                                              start_day=start_day,
                                              end_day=end_day,
                                              daily_stats=daily_stats,
                                              sum=sum)
        return (daily_stats, sum)

    @classmethod
    @requires_mongo
    def get_daily_counts_single_month(cls,
                                      pub_id='*',
                                      adv_id='*',
                                      year_month=None,
                                      start_day=None,
                                      end_day=None,
                                      daily_stats=None,
                                      sum=None):
        """
        Populates results with stats for year_month-start_day through 
        year_month-end_day (inclusive). 
        """
        key = StatsModel.get_primary_key(year_month, pub_id, adv_id)
        # excluding hour_counts as they are large and not currently necessary
        stats_model = StatsModel.objects(_id=key).exclude('hour_counts').first()\
            or StatsModel(dt=year_month)
        for day in xrange(start_day, end_day + 1): 
            # init counts to 0 for all fields in cls._count_fields
            day_stats = dict([(k, 0) for k in cls._count_fields.keys()]) 
            counts = stats_model.day_counts.get(str(day), Counts())
            for k in day_stats.keys():
                inc_val = getattr(counts, cls._count_fields[k])
                day_stats[k] += inc_val
                sum[k] += inc_val
            day_stats['date'] = "%s-%02d" % (year_month, day)
            daily_stats.append(day_stats)
                
    @classmethod
    @requires_mongo
    def create_stats_model(cls, id, update_params):
        """
        Create stats model and save/update according to update_params
        """

        (dt, pub_id, adv_id) = id.split(":")
        stats_model = StatsModel(dt=dt,
                                 pub_id=pub_id,
                                 adv_id=adv_id)
        stats_model.save()
        StatsModel.objects(_id=id).update(**update_params)
    
    @classmethod
    def get_update_params(cls, fields, day, hour):
        """
        Updates are done for a given day and hour. Update commands
        sent to mongo are of the form:

          inc__MAPFIELD__KEY__FIELD

          where: 
            MAP_FIELD: the map of counts to be updated (day_counts/hour_counts)
            KEY: key into MAPFIELD where the udpate will occur
            FIELD: field of the element at ARRAY_FIELD[INDEX] that is 
               to be updated
        
        The function loops through all field/increment pairs provided in
        fields param and generates all the update commands. For example, 
        if fields = {'req' : 1, 'imp' : 2}, day=1, hour=1 the generated params will look like:
        
        {'inc__day_counts__0__req': 1, 
         'inc__day_counts__0__imp': 2, 
         'inc__hour_counts__0:1__req': 1, 
         'inc__hour_counts__0:1__imp': 2
        }
        
        These params are sent directly into mongoengine to perform atomic updates
        http://mongoengine.org/docs/v0.5/guide/querying.html#atomic-updates

        Note: currently assuming that increment is the only operation that will
        be done when updating. This restriction can be relaxed if necessary
        """
        params = {}
        update_param_template = "inc__%s__%s__%s" # assuming only increment
        for field, incr in fields.items():
            cur_day_key = update_param_template % \
                ("day_counts", day, cls._count_fields[field])
            cur_hour_key = update_param_template % \
                ("hour_counts", "%s:%s" % (day, hour), cls._count_fields[field])
            params[cur_day_key] = incr
            params[cur_hour_key] = incr
        return params

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
    """
    while start <= end:
        if (start.year == end.year and start.month == end.month):
            #final month in sequence, end day will be end.day
            yield (start.year, start.month, start.day, end.day)
        else:
            #not final month in sequence, so include until end of month
            yield (start.year, start.month, start.day, 
                   monthrange(start.year, start.month)[1])
        start = date(start.year, start.month, 1) + relativedelta(months=+1)

def _get_ids(dt, pub_list, adv_list):
    """
    Takes in two lists and generates ids with all possible
    pairs between the two lists
    """
    year_month = "%s-%02d" % (dt.year, dt.month)
    return [StatsModel.get_primary_key(year_month,pub, adv) 
            for pub in pub_list
            for adv in adv_list]

                       
    
