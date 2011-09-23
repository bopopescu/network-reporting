import json
from utils.decorators import web_dec
from datetime import datetime
import tornado.web
from query_managers import StatsModelQueryManager
from utils.helpers import get_datetime_from_str

class StatsUpdateHandler(tornado.web.RequestHandler):
    @web_dec
    def get(self, 
            creative=None,
            adgroup=None,
            campaign=None,
            adunit=None,
            app=None,
            date_hour=None,
            fields='{}'):

        try:
            date_hour = get_datetime_from_str(date_hour)
            fields = json.loads(fields)
        except:
            self.write("bad date or json fields")
        else:
            StatsModelQueryManager.update_counts(creative_id=creative, 
                                                 adgroup_id=adgroup, 
                                                 campaign_id=campaign,
                                                 adunit_id=adunit,
                                                 app_id=app,
                                                 date_hour=date_hour,
                                                 fields=fields)
        self.write("ok")

