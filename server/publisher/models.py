from google.appengine.ext import db
from google.appengine.api import users

from account.models import Account
from advertiser.models import Creative

# 
# A mobile app, which can have multiple Sites on which ads can be displayed
#
class App(db.Model):
  account = db.ReferenceProperty(Account)

  name = db.StringProperty(required=True)
  adsense_app_name = db.StringProperty()
  millennial_placement_id = db.StringProperty()
  
  app_type = db.StringProperty(required=True, default="iphone", choices=["iphone", "android", "ipad"])
  description = db.TextProperty()
  url = db.StringProperty()
  package = db.StringProperty()
  
  icon = db.BlobProperty()
  
  deleted = db.BooleanProperty(default=False)

  t = db.DateTimeProperty(auto_now_add=True)
  
  exchange_creative = db.ReferenceProperty(Creative)

class Site(db.Model):
  app_key = db.ReferenceProperty(App)
  account = db.ReferenceProperty(Account)
  
  # TODO: figure out how to expose this
  adsense_channel_id = db.StringProperty()
  
  name = db.StringProperty(required=True)
  url = db.StringProperty()
  description = db.TextProperty()

  width = db.FloatProperty()
  height = db.FloatProperty()
  
  format = db.StringProperty() #TODO: we should use this w/o explicity using height, width

  deleted = db.BooleanProperty(default=False)
  
  # what kind of ad is preferred here
  ad_type = db.StringProperty(required=True, choices=["text", "image"], default="image")
  
  # additional keywords that are passed to the auction
  keywords = db.TextProperty()                          
  
  # color scheme
  color_border = db.StringProperty(required=True, default='336699')
  color_bg = db.StringProperty(required=True, default='FFFFFF')
  color_link = db.StringProperty(required=True, default='0000FF')
  color_text = db.StringProperty(required=True, default='000000')
  color_url = db.StringProperty(required=True, default='008000')
  
  # creation time
  t = db.DateTimeProperty(auto_now_add=True)
  
  # Allows the site to reject ads if their eCPM does not 
  # exceed a given threshold, on a per-priority level basis
  def threshold_cpm(self, priority_level):
    return 0
  
  def _get_app(self):
      return self.app_key
  def _set_app(self, value):
      self.app_key = value
  app = property(_get_app, _set_app)
    
    
  @classmethod
  def site_by_id(c, id):
    if id.startswith("ca"):
      account = Account.gql("where adsense_pub_id = :1", id).get()
      s = Site.gql("where account = :1", account).get()
    else:
      s = Site.get(id)      
    return s
