from advertiser.models import Creative
from publisher.models import Site as AdUnit


def get_ctr(adunit, creative):
    """ Returns the appropriate click through rate for a given adunit-creative
    pair. Calculates the rate if necessary, always using a sample size of at 
    least 1000 impressions. Updates the CTR every hour if possible."""
    
    SAMPLE_SIZE = 1000
    DEFAULT_CTR = 0.03 # If we have no information, we use the default CTR
    
    timely_cache_ctr = _get_ctr_from_memcache(adunit, creative)
    
    if timely_cache_ctr is not None:
        return timely_cache_ctr
        
    _update_memcache_ctr(adunit, creative)
        

def _get_ctr_from_memcache(adunit, creative, dt=datetime.datetime.now()):
    """ Returns the ctr for a given adunit-creative dt """
    pass
    
def _update_memcache_ctr(adunit, creative, dt=datetime.datetime.now()): )