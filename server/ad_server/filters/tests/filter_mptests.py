import os
import sys

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from advertiser.models import AdGroup
from ad_server.filters.filters import kw_filter, format_filter

from publisher.models import Site as AdUnit
from advertiser.models import Creative


def kw_filter_mptest():
    adgroup = AdGroup(keywords=[('m_age:19 AND m_gender:m'), # OR
                                ('m_age:20 AND m_gender:f')])
    
    # True means this filter would like to reject the value                            
    inputs_expected = {('m_age:19','m_gender:m','color:blue'):True,
                       ('m_age:22','m_gender:f','color:blue'):False,
                       ('m_age:19','m_gender:f'):False,
                       ('m_age:20','m_gender:f','color:green'):True,
                      }
    
    for keywords,match in inputs_expected.iteritems():
        f,log_message,removed_list = kw_filter(keywords)
        print keywords, f(adgroup)
        assert f(adgroup) == match
        
def custom_format_filter_mptest():
    adunit1 = AdUnit(format="custom", custom_width=120, custom_height=200)
    adunit2 = AdUnit(format="custom", custom_width=320, custom_height=50)
    adunit3 = AdUnit(format="320x50")
    creative1 = Creative(format="custom", custom_width=120, custom_height=200)
    creative2 = Creative(format="custom", custom_width=320, custom_height=50)
    creative3 = Creative(format="320x50")
    real_filter1, msg, l = format_filter(adunit1)
    real_filter2, msg, l = format_filter(adunit2)
    real_filter3, msg, l = format_filter(adunit3)
    assert(real_filter1(creative1))
    assert(not real_filter1(creative2))
    assert(real_filter2(creative2))
    assert(not real_filter2(creative3))
    assert(not real_filter3(creative2))
    
def landscape_format_filter_mptest():
    adunit1 = AdUnit(format="full", landscape=True)
    adunit2 = AdUnit(format="full", landscape=False)
    adunit3 = AdUnit(format="full_tablet", landscape=True)
    adunit4 = AdUnit(format="full_tablet", landscape=False)

    creative1 = Creative(format="full", landscape=True)
    creative2 = Creative(format="full", landscape=False)
    creative3 = Creative(format="full_tablet", landscape=True)
    creative4 = Creative(format="full_tablet", landscape=False)
    
    real_filter1, msg, l = format_filter(adunit1)
    real_filter2, msg, l = format_filter(adunit2)
    real_filter3, msg, l = format_filter(adunit3)
    real_filter4, msg, l = format_filter(adunit4)

    assert(real_filter1(creative1))
    assert(not real_filter1(creative2))
    assert(not real_filter1(creative3))
    assert(not real_filter1(creative4))

    assert(real_filter2(creative2))
    assert(not real_filter2(creative1))
    assert(not real_filter2(creative3))
    assert(not real_filter2(creative4))

    assert(real_filter3(creative3))
    assert(not real_filter3(creative1))
    assert(not real_filter3(creative2))
    assert(not real_filter3(creative4))

    assert(real_filter4(creative4))
    assert(not real_filter4(creative1))
    assert(not real_filter4(creative2))
    assert(not real_filter4(creative3))

def horrible_geo_system_mptest():
    """ Right now we store the country tuple in a custom string encoding. """ 
    
    # I want this adunit to accept everything
    adunit1 = AdUnit()
    creative1 = Creative(format="full", landscape=True)

    
    real_filter1, msg, l = format_filter(country_tuple)

    assert(real_filter1(creative1))
    
    

