import datetime   
from common.utils.marketplace_helpers import get_width_and_height      
from common.utils.helpers import to_uni, to_ascii    

class ClientContext(object):
    """ All of the information provided to us by the client.
    
        Along with adunit context, this provides all the necessary information
        for running a battle. """
    def __init__ (self,
                  adunit=None,
    	          keywords=None,
                  country_code=None, # Two characater country code.
                  region_code=None, # For future use.
    	          excluded_adgroup_keys=[],
    	          raw_udid=None, 
    	          mopub_id=None,
    	          ll=None,
    	          request_id=None,
    	          now=datetime.datetime.now(),
    	          user_agent=None,  
    	          geo_predicates=["country_name=US","country_name=*"],   #TODO get rid of this horrible hack. Refactor geopreds!   
    	          experimental=None,
    	          client_ip=None,
    	          ):         
        self.adunit = adunit
        self.keywords = keywords
        self.country_code = country_code
        self.region_code = region_code
        self.excluded_adgroup_keys = excluded_adgroup_keys
        self.raw_udid = raw_udid
        self.mopub_id = mopub_id
        self.ll = ll
        self.request_id = request_id
        self.now = now
        self.user_agent = user_agent
        self.experimental = experimental  
        self.geo_predicates = geo_predicates
        self.client_ip = client_ip        
        
        
    @classmethod
    def from_request(cls, request):
        """ Builds a client_context object based off of client's request. """    
        client_context = ClientContext()
        # Do things
        
        return client_context    
        
        
    def make_marketplace_dict(self, adunit_context):
        return build_marketplace_dict(adunit_context.adunit,
                                      self.keywords,
                                      self.raw_udid,
                                      self.user_agent,
                                      self.ll,
                                      self.client_ip,
                                      adunit_context,
                                      self.country_code)
            
        
        
        
        

def build_marketplace_dict(adunit, kws, udid, ua, ll, ip, adunit_context, country):
        app = adunit.app_key
        adunit_width, adunit_height = get_width_and_height(adunit)
        if app.primary_category == "not_selected":
            primary_category = None
        else:
            primary_category = app.primary_category
        if app.secondary_category == "not_selected":
            secondary_category = None
        else:
            secondary_category = app.secondary_category
        ret =  dict(adunit_id = str(adunit.key()),
                    format = adunit.format,
                    mopub_id = udid,
                    user_keywords = None,
                    keywords = kws,
                    latlng = ll,
                    user_agent = ua,
                    ip = ip,
                    app_id = str(app.key()),
                    global_app_id = app.global_id or None,
                    app_name = app.name,
                    #app_domain = app.package if app.app_type in ('iphone', 'ipad') else None,
                    pub_id = str(app.account.key()),
                    pub_name = app.account.company,
                    pub_domain = app.account.domain,
                    pub_rev_share = app.account.network_config.rev_share,
                    price_floor = app.account.network_config.price_floor,
                    primary_category = primary_category, 
                    secondary_category = secondary_category,
                    #app_bundle = app.package if app.app_type == 'android' else None,
                    # These return 0 if interstitial or w/e, don't return 0 just None
                    width = adunit_width,
                    height = adunit_height,
                    paid = 0,
                    country = country,
                    )
        none_keys = []
        for k,v in ret.iteritems():
            if v is None:
                none_keys.append(k) 
            ret[k] = to_ascii(v)
        for key in none_keys:
            del(ret[key])
        return ret
