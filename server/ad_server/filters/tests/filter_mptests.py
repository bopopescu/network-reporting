import os
import sys

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from advertiser.models import AdGroup
from ad_server.filters.filters import kw_filter

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
