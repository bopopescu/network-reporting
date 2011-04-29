import logging

from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from account.models import Account
# from budget import budget_service
#
# A campaign.    Campaigns have budgetary and time based restrictions.    
# 
class Campaign(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    campaign_type = db.StringProperty(choices=['gtee', 'gtee_high', 'gtee_low', 'promo', 'network','backfill_promo'], default="network")

    # budget per day
    budget = db.FloatProperty() 
    
    timeslice_snapshot = db.FloatProperty()
    
    # budget per timeslice, determined dynamically
    timeslice_budget = db.FloatProperty()
    
    budget_strategy = db.StringProperty(choices=['evenly','allatonce'], default="allatonce")
    
    # start and end dates 
    start_date = db.DateProperty()
    end_date = db.DateProperty()
    
    active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)
    
    # who owns this
    u = db.UserProperty() 
    account = db.ReferenceProperty(Account)
    t = db.DateTimeProperty(auto_now_add=True)

    @property
    def owner_key(self):
        return None

    @property
    def owner_name(self):
        return None 
    
    def get_owner(self):
        return None
        
    def set_owner(self, value):
        pass
            
    def owner(self):
        return property(get_owner, set_owner)

    def delivery(self):
        if self.stats: return self.stats.revenue / self.budget
        else: return 1

        
        
class AdGroup(db.Model):
    campaign = db.ReferenceProperty(Campaign,collection_name="adgroups")
    net_creative = db.ReferenceProperty(collection_name='creative_adgroups')
    name = db.StringProperty()
    
    # start and end dates 
    start_date = db.DateProperty()
    end_date = db.DateProperty()
    
    created = db.DateTimeProperty(auto_now_add=True)

    # the priority level at which this ad group should be auctioned
    priority_level = db.IntegerProperty(default=1)
    network_type = db.StringProperty(choices=["adsense", "iAd", "admob","millennial","appnexus","inmobi","mobfox","jumptap","brightroll","greystripe", "custom"])

    # Note that bid has different meaning depending on the bidding strategy.
    # if CPM: bid = cost per 1000 impressions
    # if CPC: bid = cost per 1 click
    bid = db.FloatProperty(default=0.05)
    bid_strategy = db.StringProperty(choices=["cpc", "cpm", "cpa"], default="cpm")

    # state of this ad group
    active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)
    
    # percent of users to be targetted
    percent_users = db.FloatProperty(default=100.0)
    allocation_percentage = db.FloatProperty(default=100.0)
    allocation_type = db.StringProperty(choices=["users","requests"])

    # frequency caps
    minute_frequency_cap = db.IntegerProperty(default=0)
    hourly_frequency_cap = db.IntegerProperty(default=0)
    daily_frequency_cap = db.IntegerProperty(default=0)
    weekly_frequency_cap = db.IntegerProperty(default=0)
    monthly_frequency_cap = db.IntegerProperty(default=0)
    lifetime_frequency_cap = db.IntegerProperty(default=0)
    
    # all keyword and category bids are tracked here
    # categories use the category:games convention
    # if any of the input keywords match the n-grams here then we 
    # trigger a match
    keywords = db.StringListProperty()

    # all placements that are considered for this ad group
    # this is a list of keys corresponding to Site objects
    site_keys = db.ListProperty(db.Key)
    
    account = db.ReferenceProperty(Account)
    t = db.DateTimeProperty(auto_now_add=True)
    
    
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
    cities = db.StringListProperty(default=[])
    
    country = db.StringProperty()
    region = db.StringProperty()
    state = db.StringProperty()
    city = db.StringProperty()
    
    # Geographic preferences are expressed as string tuples that can match
    # the city, region or country that is resolved via reverse geocode at 
    # request time.    If the list is blank, any value will match. If the list
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
    
    def default_creative(self, custom_html=None):
        c = None
        if self.network_type == 'adsense': c = AdSenseCreative(name="adsense dummy",ad_type="adsense", format="320x50", format_predicates=["format=*"])
        elif self.network_type == 'iAd': c = iAdCreative(name="iAd dummy",ad_type="iAd", format="320x50", format_predicates=["format=320x50"])
        elif self.network_type == 'admob': c = AdMobCreative(name="admob dummy",ad_type="admob", format="320x50", format_predicates=["format=320x50"])
        elif self.network_type == 'brightroll': c = BrightRollCreative(name="brightroll dummy",ad_type="html_full", format="full",format_predicates=["format=*"])
        elif self.network_type == 'jumptap': c = JumptapCreative(name="jumptap dummy",ad_type="html", format="320x50",format_predicates=["format=320x50"])
        elif self.network_type == 'millennial': c = MillennialCreative(name="millennial dummy",ad_type="html",format="320x50", format_predicates=["format=320x50"]) # TODO: make sure formats are right
        elif self.network_type == 'inmobi': c = InMobiCreative(name="inmobi dummy",ad_type="html",format="320x50", format_predicates=["format=320x50"]) # TODO: make sure formats are right
        elif self.network_type == 'greystripe' : c = GreyStripeCreative(name="greystripe dummy",ad_type="greystripe", format="320x50", format_predicates=["format=*"]) # TODO: only formats 320x320, 320x48, 300x250
        elif self.network_type == 'appnexus': c = AppNexusCreative(name="appnexus dummy",ad_type="html",format="320x50",format_predicates=["format=300x250"])
        elif self.network_type == 'mobfox' : c = MobFoxCreative(name="mobfox dummy",ad_type="html",format="320x50",format_predicates=["format=320x50"])
        elif self.network_type == 'custom': c = CustomCreative(name='custom', ad_type='html', format='', format_predicates=['format=*'], html_data=custom_html) 
        
        if c: c.ad_group = self
        return c
    
    def __repr__(self):
        return "AdGroup:'%s'" % self.name
        
    @property
    def geographic_predicates(self):
        return self.geo_predicates
        
    def get_owner(self):
        return self.campaign

    def set_owner(self, value):
        self.campaign = value
            
    def owner(self, value):
        return property(get_owner, set_owner)

    @property
    def owner_key(self):
        return self._campaign

    @property
    def owner_name(self):
        return 'campaign'
        
    @property
    def cpc(self):
        if self.bid_strategy == 'cpc':
            return self.bid
        return None
        
    @property
    def cpm(self):
        if self.bid_strategy == 'cpm':
            return self.bid
        return None
 
class Creative(polymodel.PolyModel):
    name = db.StringProperty()
    
    ad_group = db.ReferenceProperty(AdGroup,collection_name="creatives")

    active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)

    # the creative type helps the ad server render the right thing if the creative wins the auction
    ad_type = db.StringProperty(choices=["text", "text_icon", "image", "iAd", "adsense", "admob", "greystripe", "html", "html_full", "clear"], default="image")

    # tracking pixel
    tracking_url = db.StringProperty()

    # destination URLs
    url = db.StringProperty()
    display_url = db.StringProperty()
    
    # conversion goals
    conv_appid = db.StringProperty()

    # format predicates - the set of formats that this creative can match
    # e.g. format=320x50
    # e.g. format=*
    format_predicates = db.StringListProperty(default=["format=*"]) 
    format = db.StringProperty(default="320x50") # We should switch to using this field instead of format_predicates: one creative per size

    # time of creation
    account = db.ReferenceProperty(Account)
    t = db.DateTimeProperty(auto_now_add=True)

    # DEPRECATED: metrics such as e_cpm and CTR only make sense within the context of matching a creative with an adunit
    # Use /ad_server/optimizer/optimizer.py instead to calculate these metrics.
    #
    # def e_cpm(self):
    #     if self.ad_group.bid_strategy == 'cpc':
    #         return float(self.p_ctr() * self.ad_group.bid * 1000)
    #     elif self.ad_group.bid_strategy == 'cpm':
    #         return float(self.ad_group.bid)

    @property
    def multi_format(self):
            return None

    # DEPRECATED: see comment above
    # predicts a CTR for this ad.    We use 1% for now.
    # TODO: implement this in a better way
    # def p_ctr(self):
    #     return 0.01
        
    
    def _get_adgroup(self):
            return self.ad_group        

    def _set_adgroup(self,value):
            self.ad_group = value
            
    adgroup = property(_get_adgroup,_set_adgroup)
            

    def get_owner(self):
        return self.ad_group

    def set_owner(self, value):
        self.ad_group = value
  
    
    def _get_width(self):
        if hasattr(self,'_width'):
            return self._width
        width = 0 
        if self.format:
            parts = self.format.split('x')
            if len(parts) == 2:
                width = parts[0]
        return width
    def _set_width(self,value):
        self._width = value
    width = property(_get_width,_set_width)      
         
    def _get_height(self):
        if hasattr(self,'_height'):
            return self._height
            
        height = 0 
        if self.format:
            parts = self.format.split('x')
            if len(parts) == 2:
                height = parts[1]
        return height
    
    def _set_height(self, value):
        self._height = value
        
    height = property(_get_height,_set_height)      
          
    
    def owner(self):
        return property(get_owner, set_owner)
           
    @property
    def owner_key(self):
        return self._ad_group
      
    @property
    def owner_name(self):
        return 'ad_group'
            
    def __repr__(self):
        return "Creative{ad_type=%s, key_name=%s}" % (self.ad_type, self.key().id_or_name())
  

class TextCreative(Creative):
    # text ad properties
    headline = db.StringProperty()
    line1 = db.StringProperty()
    line2 = db.StringProperty()

    def __repr__(self):
        return "'%s'" % (self.headline,)

class TextAndTileCreative(Creative):
    line1 = db.StringProperty()
    line2 = db.StringProperty()
    image = db.BlobProperty()
    action_icon = db.StringProperty(choices=["download_arrow4", "access_arrow", "none"], default="download_arrow4")
    color = db.StringProperty(default="000000")
    font_color = db.StringProperty(default="FFFFFF")
    gradient = db.BooleanProperty(default=False)

class HtmlCreative(Creative):
    # html ad properties
    # html_name = db.StringProperty(required=True)
    html_data = db.TextProperty()

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

class CustomCreative(HtmlCreative):
    pass

class iAdCreative(Creative):
    @property
    def multi_format(self):
        return ('728x90', '320x50',)
    
class AdSenseCreative(Creative):
    pass

class AdMobCreative(Creative):
    pass

class MillennialCreative(Creative):
    
    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250',)
   
class InMobiCreative(Creative):
   
    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250', '468x60', '120x600',)
    
class AppNexusCreative(Creative):
    pass  

class BrightRollCreative(Creative):
    pass

class JumptapCreative(Creative):
    pass

class GreyStripeCreative(Creative):
   
    @property
    def multi_format(self):
        return ('320x320', '320x50', '300x250',)
    
class MobFoxCreative(Creative):
    pass
  
  
class NullCreative(Creative):
    pass

class TempImage(db.Model):
    image = db.BlobProperty()

