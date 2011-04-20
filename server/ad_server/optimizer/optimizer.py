from advertiser.models import Creative
from publisher.models import Site as AdUnit
import datetime
import logging

def get_ctr(adunit_context, creative, min_sample_size=1000, default_ctr=0.03, dt=datetime.datetime.now()):
    """ Returns the appropriate click through rate for a given adunit-creative
    pair. Calculates the rate if necessary, always uses a sample size of at 
    least 1000 impressions."""

    # Get adunit bundled with additional context - Note: this is passed in
    # adunit_bundle = AdUnitQueryManager(adunit.key()).get_adunit()
    
    hourly_ctr = adunit_context._get_ctr(creative, 
                                  min_sample_size=min_sample_size, 
                                  date_hour=dt)
    
    # If there is a valid hourly ctr, return it
    if not hourly_ctr is None:
        return hourly_ctr
    
    # If there is no valid hourly ctr fall back to daily
    daily_ctr = adunit_context._get_ctr(creative, 
                                  min_sample_size=min_sample_size, 
                                  date=dt.date())
                                  
    if not daily_ctr is None:
        return daily_ctr
        
    else:
        return default_ctr
        
        
def get_ecpm(adunit_context, creative, min_sample_size=1000, default_ctr=0.03, dt=datetime.datetime.now()):
    if creative.ad_group.cpc is not None:
        ctr = get_ctr(adunit_context, creative, min_sample_size, default_ctr, dt)
        return float(ctr * creative.ad_group.cpc * 1000) 
    elif creative.ad_group.cpm is not None:
        return float(creative.ad_group.cpm) 