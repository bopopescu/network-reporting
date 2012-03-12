import datetime
import random

from ad_server.adunit_context.adunit_context import CreativeCTR
from ad_server.debug_console import trace_logging

SAMPLING_FRACTION = .03 # We use a default sampling rate of 3 per 100
SAMPLING_ECPM = .50 # We use 50 cents as a representative ecpm
DEFAULT_CTR=0.005 # 0.5% CTR is rather fair


# Some convenience functions that are ONLY for testing:
def get_ctr(adunit_context, creative, min_sample_size=1000, default_ctr=DEFAULT_CTR, dt=datetime.datetime.now()):
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
        
    # # If there is no valid daily ctr, fall back to weekly
    # weekly_ctr = adunit_context._get_ctr_for_week(creative,
    #                                 min_sample_size=min_sample_size,
    #                                 week_end_date = dt.date())
    # 
    # if not weekly_ctr is None:
    #     return weekly_ctr
    # 
    else:
        return default_ctr
        
def get_ecpm(adunit_context, creative, min_sample_size=1000, default_ctr=DEFAULT_CTR, dt=datetime.datetime.now()):
    if creative.ad_group.cpc is not None:
        ctr = get_ctr(adunit_context, creative, min_sample_size, default_ctr, dt)
        return float(ctr * creative.ad_group.cpc * 1000) 
    elif creative.ad_group.cpm is not None:
        return float(creative.ad_group.cpm) 
        
def get_ecpm_for_test(adunit, creative, dt = None):
    """ For testing, we never want to switch to sampling mode."""
    result_dict = get_ecpms(adunit, [creative], sampling_fraction = 0, dt_now = dt)
    return result_dict[creative]


# The real functions for use in production:
        
def get_ecpms(adunit_context, creatives, sampling_fraction=SAMPLING_FRACTION, sampling_ecpm=SAMPLING_ECPM):
    """ Returns a dict: k=creative, v=ecpm, 
    With some probability, it instead returns a constant for all values"""
    rand_dec = random.random()
    use_sampling_constant = (rand_dec < sampling_fraction)
    ecpm_dict = {}
    if use_sampling_constant:
        trace_logging.warning("Sampled from adunit: %s - Using default ecpms" % str(adunit_context.adunit.key()))
        for c in creatives:
            ecpm_dict[c] = sampling_ecpm
    else:
        trace_logging.info("calculating ecpms for adunit creatives:")
        for c in creatives:
            ecpm = get_ecpm(adunit_context, c)
            creative_name = c.name or 'None'
            trace_logging.info("    %s: %s" % (creative_name.encode('utf8'), str(ecpm)))
            ecpm_dict[c] = ecpm
        
    return ecpm_dict

def calculate_ecpm(creative_ctr, creative, min_sample_size = 1000, default_ctr = DEFAULT_CTR, dt_now = None):
    """ The dt_now argument is only used for testing."""
    if creative.ad_group.cpc is not None:
        ctr = creative_ctr.get_ctr(default_ctr = default_ctr, min_sample_size = min_sample_size, dt_now = dt_now)
        return float(ctr * creative.ad_group.cpc * 1000)
    elif creative.ad_group.cpm is not None:
        return float(creative.ad_group.cpm)
    else:
        return None

