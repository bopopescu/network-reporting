from advertiser.models import Creative
from publisher.models import Site as AdUnit
import datetime
import logging
import random

from ad_server.debug_console import trace_logging

SAMPLING_FRACTION = .03 # We use a default sampling rate of 3 per 100
SAMPLING_ECPM = .50 # We use 50 cents as a representative ecpm

def get_ctr(adunit_context, creative, min_sample_size=1000, default_ctr=0.03, dt=datetime.datetime.now()):
    """ Returns the appropriate click through rate for a given adunit-creative
    pair. Calculates the rate if necessary, always uses a sample size of at 
    least 1000 impressions."""

    # Get adunit bundled with additional context - Note: this is passed in
    
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
        
        
def get_ecpms(adunit_context, creatives, sampling_fraction=SAMPLING_FRACTION, sampling_ecpm=SAMPLING_ECPM):
    """ Returns a dict: k=creative, v=ecpm, 
    With some probability, it instead returns a constant for all values"""
    rand_dec = random.random()
    use_sampling_constant = (rand_dec < sampling_fraction)
    ecpm_dict = {}
    trace_logging.warning("Sampled from adunit: %s" % str(adunit_context.adunit.key()))
    if use_sampling_constant:
        for c in creatives:
            ecpm = sampling_ecpm
            ecpm_dict[c] = ecpm
    else:
        for c in creatives:
            ecpm = get_ecpm(adunit_context, c)
            ecpm_dict[c] = ecpm
        
    return ecpm_dict