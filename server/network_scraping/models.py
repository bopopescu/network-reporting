from google.appengine.ext import db
from publisher.models import AdUnit, App
from account.models import Account

class NetworkScrapeRecord(db.model):
    datetime = db.DateTimeProperty(required=True)
    network = db.StringProperty(required=True)
    impressions = db.IntegerProperty()
    clicks = db.IntegerProperty()
    net_revenue = db.FloatProperty()
    requests = db.IntegerProperty()
    cpc = db.FloatProperty()
    #adunit = db.ReferenceProperty(AdUnit)
    #app = db.ReferenceProperty(App)
    adunit_name = db.StringProperty()
    app_name = db.StringProperty()
    
class NetworkCredential(db.model):
    account = db.ReferenceProperty(Account)
    #app = db.ReferenceProperty(App)
    app_name = db.StringProperty()
    username = db.StringProperty()
    password = db.StringProperty()
    network = db.StringProperty()