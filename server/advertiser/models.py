from google.appengine.ext import db
from google.appengine.ext.db import polymodel

#
# A campaign.  Campaigns have budgetary and time based restrictions.  
# 
class Campaign(db.Model):
  name = db.StringProperty()
  description = db.TextProperty()
  campaign_type = db.StringProperty(choices=['gtee', 'promo', 'network'], default="network")

  # daily budget
  budget = db.FloatProperty() 
  
  # start and end dates 
  start_date = db.DateProperty()
  end_date = db.DateProperty()
  
  active = db.BooleanProperty(default=True)
  deleted = db.BooleanProperty(default=False)
  
  # who owns this
  u = db.UserProperty() 
  t = db.DateTimeProperty(auto_now_add=True)
  
  def delivery(self):
    if self.stats: return self.stats.revenue / self.budget
    else: return 1
    
class AdGroup(db.Model):
  campaign = db.ReferenceProperty(Campaign)
  name = db.StringProperty()
  
  created = db.DateTimeProperty(auto_now_add=True)

  # the priority level at which this ad group should be auctioned
  priority_level = db.IntegerProperty(default=1)
  network_type = db.StringProperty(choices=["adsense", "iAd", "admob"])

  bid = db.FloatProperty()
  bid_strategy = db.StringProperty(choices=["cpc", "cpm", "cpa"], default="cpm")

  # state of this ad group
  active = db.BooleanProperty(default=True)
  deleted = db.BooleanProperty(default=False)
  
  
  # percent of users to be targetted
  percent_users = db.FloatProperty(default=100.0)

  # all keyword and category bids are tracked here
  # categories use the category:games convention
  # if any of the input keywords match the n-grams here then we 
  # trigger a match
  keywords = db.StringListProperty()

  # all placements that are considered for this ad group
  # this is a list of keys corresponding to Site objects
  site_keys = db.ListProperty(db.Key)
  
  DEVICE_CHOICES = (
    ('any','Any'),
    ('iphone','iPhone'),
    ('ipod','iPod Touch'),
    ('ipad','iPad'),
    ('android','Android'),
    ('blackberry','Blackberry'),
    ('windows7','Windows Phone 7'),
  )
  devices = db.StringListProperty(default=['any'])
  
  MIN_OS_CHOICES = (
    ('any','Any'),
    ('iphone__2_0','2.0+'),
    ('iphone__2_1','2.1+'),
    ('iphone__3_0','3.0+'),
    ('iphone__3_1','3.1+'),
    ('iphone__3_2','3.2+'),
    ('iphone__4_0','4.0+'),
    ('iphone__4_1','4.1+'),
  )
  min_os = db.StringListProperty(default=['any'])
  
  
  USER_TYPES = (
    ('any','Any'),
    ('active_7','7 day active user'),
    ('active_15','15 day active user'),
    ('active_30','30 day active user'),
    ('inactive_7','7 day active user'),
    ('inactive_15','15 day active user'),
    ('inactive_30','30 day inactive user'),
  )
  
  active_user = db.StringListProperty(default=['any'])
  active_app = db.StringListProperty(default=['any'])
  
  country = db.StringProperty()
  state = db.StringProperty()
  city = db.StringProperty()
  
  # Geographic preferences are expressed as string tuples that can match
  # the city, region or country that is resolved via reverse geocode at 
  # request time.  If the list is blank, any value will match. If the list
  # is not empty, the value must match one of the elements of the list.
  # 
  # Valid predicates are:
  # city_name=X,region_name=X,country_name=X
  # region_name=X,country_name=X
  # country_name=X
  # zipcode=X
  #
  # Each incoming request will be matched against all of these combinations
  geo_predicates = db.StringListProperty(default=["country_name=*"])
  
  # Device and platform preferences are listed similarly:
  #
  # model_name=X,brand_name=X
  # brand_name=X,platform_name=X
  # platform_name=X
  device_predicates = db.StringListProperty(default=["platform_name=*"])
  
  def __cmp__(self,other):
    return self.key().__cmp__(other.key())
  
  def default_creative(self):
    c = None
    if self.network_type == 'adsense': c = AdSenseCreative(ad_type="adsense", format_predicates=["format=*"])
    elif self.network_type == 'iAd': c = iAdCreative(ad_type="iAd", format_predicates=["format=320x50"])
    elif self.network_type == 'admob': c = AdMobCreative(ad_type="admob", format_predicates=["format=320x50"])
    
    if c: c.ad_group = self
    return c
  
  def __repr__(self):
    return "AdGroup:'%s'" % self.name

class Creative(polymodel.PolyModel):
  ad_group = db.ReferenceProperty(AdGroup)

  active = db.BooleanProperty(default=True)
  deleted = db.BooleanProperty(default=False)

  # the creative type helps the ad server render the right thing if the creative wins the auction
  ad_type = db.StringProperty(choices=["text", "image", "iAd", "adsense", "admob", "html", "clear"], default="text")

  # destination URLs
  url = db.StringProperty()
  display_url = db.StringProperty()

  # format predicates - the set of formats that this creative can match
  # e.g. format=320x50
  # e.g. format=*
  format_predicates = db.StringListProperty(default=["format=*"]) 

  # time of creation
  t = db.DateTimeProperty(auto_now_add=True)

  # calculates the eCPM for this creative, based on 
  # the CPM bid for the ad group or the CPC bid for the ad group and the predicted CTR for this
  # creative
  def e_cpm(self):
    if self.ad_group.bid_strategy == 'cpc':
      return self.p_ctr() * self.ad_group.bid * 1000
    elif self.ad_group.bid_strategy == 'cpm':
      return self.ad_group.bid

  # predicts a CTR for this ad.  We use 1% for now.
  # TODO: implement this in a better way
  def p_ctr(self):
    return 0.01

  def __repr__(self):
    return "Creative{ad_type=%s, eCPM=%.02f}" % (self.ad_type, self.e_cpm())

class TextCreative(Creative):
  # text ad properties
  headline = db.StringProperty()
  line1 = db.StringProperty()
  line2 = db.StringProperty()
  
  def __repr__(self):
    return "'%s'" % (self.headline,)

class HtmlCreative(Creative):
  # html ad properties
  html_name = db.StringProperty(required=True, default="Demo HTML Creative")
  html_data = db.TextProperty(default="<style type=\"text/css\">body {font-size: 12px;font-family:helvetica,arial,sans-serif;margin:0;padding:0;text-align:center} .creative_headline {font-size: 18px;} .creative_promo {color: green;text-decoration: none;}</style><div class=\"creative_headline\">Welcome to mopub!</div><div class=\"creative_promo\">This is a test ad</div><div>You can now set up a new campaign to serve other ads.</div>")

class ImageCreative(Creative):
  # image properties
  image = db.BlobProperty()
  image_width = db.IntegerProperty()
  image_height = db.IntegerProperty()

  @classmethod
  def get_format_predicates_for_image(c, img):
    IMAGE_PREDICATES = {"300x250": "format=300x250", 
      "320x50": "format=320x50", 
      "300x50": "format=320x50", 
      "728x90": "format=728x90",
      "468x60": "format=468x60"}
    fp = IMAGE_PREDICATES.get("%dx%d" % (img.width, img.height))
    return [fp] if fp else None

class iAdCreative(Creative):
  pass
    
class AdSenseCreative(Creative):
  pass

class AdMobCreative(Creative):
  pass
    
class NullCreative(Creative):
  pass
  
