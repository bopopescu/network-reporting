from advertiser.models import Creative
from publisher.models import Site as AdUnit
import datetime

def get_ctr(adunit, creative, min_sample_size=1000, default_ctr=0.03):
    """ Returns the appropriate click through rate for a given adunit-creative
    pair. Calculates the rate if necessary, always using a sample size of at 
    least 1000 impressions. Updates the CTR every hour if possible."""
    
    current_hour_ctr = _hour_ctr(adunit, creative, min_sample_size, default_ctr)
    
    if current_hour_ctr is not None:
        return current_hour_ctr
        
    # Either the current hour ctr was never set or an hour has elapsed
    _calculate_hour_ctr()
        
    _update_memcache_ctr(adunit, creative)
        

def _hour_ctr(adunit, creative):
    """ Returns the ctr for a given adunit-creative dt """
    memcache.get()
    
def _update_memcache_ctr(adunit, creative, dt=datetime.datetime.now()): 
    pass