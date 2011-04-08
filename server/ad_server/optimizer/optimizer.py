from advertiser.models import Creative
from publisher.models import Site as AdUnit
import datetime

def get_ctr(adunit_bundle, creative, min_sample_size=1000, default_ctr=0.03, 
            dt=datetime.datetime.now()):
    """ Returns the appropriate click through rate for a given adunit-creative
    pair. Calculates the rate if necessary, always using a sample size of at 
    least 1000 impressions. Updates the CTR every hour if possible."""

    cur_hour = dt.hour
    prev_hour = (dt - datetime.timedelta(hour=1)).hour

    # Get adunit bundled with additional context
    adunit_bundle = AdUnitQueryManager(adunit.key()).get_adunit()
    
    # Check if there is a precalculated ctr for the current hour
    creatives = adunit_bundle.eligible_creatives
    creative = [b_c for b_c in creatives if (b_c.key() == creative.key())]
    
    cur_hour_attr_name = "hour-%s-ctr" % cur_hour
    prev_hour_attr_name = "hour-%s-ctr" % prev_hour
    
    # Check if there is a value for the current hour
    if hasattr(b_creative, cur_hour_attr_name):
        return b_creative.cur_hour_attr_name

    # If there is no value for the current hour, we calculate it
    cur_hour_imps = 1200 # TODO: placeholder
    
    # Check if there are enough impressions in the hour
    if cur_hour_imps >= min_sample_size:
        cur_ctr
        setattr(b_creative, cur_hour_attr_name, cur_ctr)   
    if hour_ctr is not None:
        return hour_ctr

    
        

def update_ctr(adunit, creative, min_sample_size=1000, default_ctr=0.03,
               dt=datetime.datetime.now())    
    
    
########### HELPER FUNCTIONS #################



def _hour_ctr(adunit, creative, min_sample_size, dt):
    """ Returns the ctr for a given adunit-creative-hour """
    

    
    memcache.get()
    
def _previous_hour_ctr(adunit, creative, min_sample_size, dt):
    """ Returns the ctr for the previous adunit-creative-hour """
    prev_hour = (dt - datetime.timedelta(hours=1)).hour
    key = _make_adunit_creative_hour_key(adunit, creative, prev_hour)
    memcache.get(key)

    
    
def _make_adunit_creative_hour_key(adunit, creative, dt):
    return ""
    
    
def _update_memcache_ctr(adunit, creative, dt=datetime.datetime.now()): 
    pass
    
def _set_ctr_in_memcache(adunit, creative, ctr, dt=datetime.datetime.now()):
    pass
    
########### TEST FUNCTIONS #################
    
def _test_get_ctr(adunit, creative, min_sample_size=5):
    get_ctr(adunit,creative,min_sample_size=min_sample_size)