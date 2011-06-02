from google.appengine.ext import db
from google.appengine.api import users

from account.models import Account, NetworkConfig
from advertiser.models import Creative

# 
# A mobile app, which can have multiple Sites on which ads can be displayed
#
class App(db.Model):
    account = db.ReferenceProperty(Account)
  
    name = db.StringProperty(required=True)
    adsense_app_name = db.StringProperty()
    
    app_type = db.StringProperty(required=True, default='iphone', choices=['iphone', 'android', 'ipad', 'mweb'])
    description = db.TextProperty()
    url = db.StringProperty()
    package = db.StringProperty()
    
    icon = db.BlobProperty()
    
    # Ad network overrides
    jumptap_app_id = db.StringProperty()
    millennial_app_id = db.StringProperty()

    deleted = db.BooleanProperty(default=False)
  
    t = db.DateTimeProperty(auto_now_add=True)
    
    exchange_creative = db.ReferenceProperty(Creative)
    
    experimental_fraction = db.FloatProperty(default=0.0)
    
    network_config = db.ReferenceProperty(NetworkConfig, collection_name="apps")
  
    def get_owner(self):
        return None
  
    def set_owner(self, value):
        pass
  
    def owner(self):
        return property(get_owner, set_owner)
    
    @property
    def owner_key(self):
        return None
    
    @property
    def owner_name(self):
        return None
  
    
class Site(db.Model):
    DEVICE_FORMAT_CHOICES = (
           u'phone',
           u'tablet',
       )
       
    FORMAT_CHOICES = (
          u'full',
          u'full_tablet',
          u'full_landscape',
          u'full_tablet_landscape',
          u'728x90',
          u'300x250',
          u'160x600',
          u'320x50',
          u'custom',
      )
    # TODO: Why is this "app_key" and not "app"?
    app_key = db.ReferenceProperty(App, collection_name="all_adunits")
    account = db.ReferenceProperty(Account)
    
    # TODO: figure out how to expose this
    adsense_channel_id = db.StringProperty()
    
    name = db.StringProperty(required=True, default='Banner Ad')
    url = db.StringProperty()
    description = db.TextProperty()
    custom_width = db.IntegerProperty()
    custom_height = db.IntegerProperty()
    
    device_format = db.StringProperty(default='phone', choices=DEVICE_FORMAT_CHOICES)
    format = db.StringProperty(choices=FORMAT_CHOICES) #TODO: we should use this w/o explicity using height, width
    resizable = db.BooleanProperty(default=False)
    landscape = db.BooleanProperty(default=False)

    deleted = db.BooleanProperty(default=False)
    
    # what kind of ad is preferred here
    ad_type = db.StringProperty(choices=['text', 'image'], default='image',required=False)
    
    # Ad network overrides
    jumptap_site_id = db.StringProperty()
    millennial_site_id = db.StringProperty()
    
    # additional keywords that are passed to the auction
    keywords = db.TextProperty() # TODO: make sure this doesn't break shit
    # keywords = db.StringListProperty()                          
    
    refresh_interval = db.IntegerProperty(default=0)
    animation_type = db.StringProperty(default='0') # NOTE: this is a string in case we don't want enumeration later
    
    # color scheme
    color_border = db.StringProperty(required=True, default='336699')
    color_bg = db.StringProperty(required=True, default='FFFFFF')
    color_link = db.StringProperty(required=True, default='0000FF')
    color_text = db.StringProperty(required=True, default='000000')
    color_url = db.StringProperty(required=True, default='008000')
    
    # creation time
    t = db.DateTimeProperty(auto_now_add=True)
    
    network_config = db.ReferenceProperty(NetworkConfig, collection_name="adunits")
    

    def threshold_cpm(self, priority_level):
        """ Allows the site to reject ads if their eCPM does not 
        exceed a given threshold, on a per-priority level basis
        TODO Make this actually do something """
        return 0
    
    def get_height(self):
        if self.height: 
            return self.height
        dimensions = self.format.split('x')
        if len(dimensions) > 1: 
            return int(dimensions[1])
        else:
            return 0

    def get_width(self):
        if self.width: 
            return self.width
        dimensions = self.format.split('x')
        if len(dimensions) > 1: 
            return int(dimensions[0])
        else:
            return 0
    
    # Now we can access app_key using app
    def _get_app(self):
        return self.app_key
    def _set_app(self, value):
        self.app_key = value
    app = property(_get_app, _set_app)
      
    @classmethod
    def site_by_id(c, id):
        if id.startswith('ca'):
            account = Account.gql('where adsense_pub_id = :1', id).get()
            s = Site.gql('where account = :1', account).get()
        else:
            s = Site.get(id)      
        return s
       
    def get_owner(self):
        return self.app_key
        
    def set_owner(self, value):
        self.app_key = value
        
    def owner(self):
        return property(get_owner, set_owner)
  
    @property
    def owner_key(self):
        return self._app_key            
  
    @property
    def owner_name(self):
        return "app_key"
        
    def get_pub_id(self, pub_id_attr):
        """ Look up the pub string in all levels """
        
        # If not found, return None
        adunit_level_id = getattr(self.network_config, pub_id_attr, None)
        if adunit_level_id:
            return adunit_level_id

        app_level_id = getattr(self.app.network_config, pub_id_attr, None)
        if app_level_id:
            return app_level_id
        
        account_level_id = getattr(self.account.network_config, pub_id_attr, None)
        if account_level_id:
            return account_level_id

###############
# rename Site #
###############

AdUnit = Site
