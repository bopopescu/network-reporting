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
            #TODO: handle converting argument to date object better
            # maybe use unix timestamp as argument?
            start_date = get_date_from_str(start_date).date()
            end_date = get_date_from_str(end_date).date()
        except:
            self.write("bad date format")
        else:
            results = StatsModelQueryManager.get_counts(pub_id=pub,
                                                        adv_id=adv,
                                                        start_date=start_date,
                                                        end_date=end_date)
            self.write(json.dumps(results))
        
        
