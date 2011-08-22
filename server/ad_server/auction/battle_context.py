import datetime
class BattleContext(object):
    """ The necessary information for running a battle. """
    def __init__ (self,
                  adunit=None,
    	          keywords=None,
                  country_tuple=[],
    	          excluded_adgroup_keys=[],
    	          udid=None,
    	          ll=None,
    	          request_id=None,
    	          now=datetime.datetime.now(),
    	          user_agent=None,  
    	          geo_predicates=["country_name=US","country_name=*"],   #TODO get rid of this horrible hack. Refactor geopreds.   
    	          experimental=None,
    	          ):         
        self.adunit = adunit
        self.keywords = keywords
        self.country_tuple = country_tuple
        self.excluded_adgroup_keys = excluded_adgroup_keys
        self.udid = udid
        self.ll = ll
        self.request_id = request_id
        self.now = now
        self.user_agent = user_agent
        self.experimental = experimental  
        self.geo_predicates = geo_predicates