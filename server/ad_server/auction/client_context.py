import datetime
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
    	          ll=None,
    	          request_id=None,
    	          now=datetime.datetime.now(),
    	          user_agent=None,  
    	          geo_predicates=["country_name=US","country_name=*"],   #TODO get rid of this horrible hack. Refactor geopreds!   
    	          experimental=None,
    	          ):         
        self.adunit = adunit
        self.keywords = keywords
        self.country_code = country_code
        self.region_code = region_code
        self.excluded_adgroup_keys = excluded_adgroup_keys
        self.raw_udid = raw_udid
        self.ll = ll
        self.request_id = request_id
        self.now = now
        self.user_agent = user_agent
        self.experimental = experimental  
        self.geo_predicates = geo_predicates