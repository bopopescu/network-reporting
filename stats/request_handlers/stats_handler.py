import json
from utils.decorators import web_dec
import tornado.web
from datetime import date, datetime
from query_managers import StatsModelQueryManager
from utils.timezones import Pacific_tzinfo
from utils.helpers import get_date_from_str

class StatsHandler(tornado.web.RequestHandler):
    @web_dec
    def get(self,
            pub='*',
            adv='*',
            start_date=None,
            end_date=None):
        try:
            start_date = get_date_from_str(start_date).date()
            end_date = get_date_from_str(end_date).date()
        except:
            self.write("bad date format")
        else:
            (daily_stats, sum) = StatsModelQueryManager.\
                get_counts(pub_id=pub,
                           adv_id=adv,
                           start_date=start_date,
                           end_date=end_date)
            results = {'status' : 200, 
                       'all_stats' : {'%s||%s' % (pub, adv) : 
                                      {"daily_stats" : daily_stats, 
                                       "sum" : sum}}}
            self.write(json.dumps(results))
        
        
