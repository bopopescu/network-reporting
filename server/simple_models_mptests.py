########## Set up Django ###########
import sys
import os
import datetime
import logging
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import unittest
from nose.tools import eq_

from simple_models import (SimpleAccount,
                           SimpleAdUnit,
                           SimpleCampaign,
                           SimpleAdGroup,
                           SimpleCreative,
                           SimpleAdUnitContext,
                           from_basic_type)



class TestBudgetEndToEnd(unittest.TestCase):

    def mptest_basic_type_conversion(self):
        simple_account = SimpleAccount(key = "test account key")
        simple_adunit = SimpleAdUnit(     key = "test adunit key",    name = "test adunit",    account = simple_account, format = {1:2, 3:4}, app_key = simple_account) # Putting a random dict in format to test plain dict functionality.
        simple_campaign = SimpleCampaign( key = "test campaign key",  name = "test campaign",  account = simple_account)
        simple_adgroup = SimpleAdGroup(   key = "test adgroup key",   name = "test adgroup",   account = simple_account, campaign = simple_campaign)
        simple_creative1 = SimpleCreative(key = "test creative1 key", name = "test creative1", account = simple_account, ad_group = simple_adgroup)
        simple_creative2 = SimpleCreative(key = "test creative2 key", name = "test creative2", account = simple_account, ad_group = simple_adgroup)
        simple_auc = SimpleAdUnitContext(adunit = simple_adunit,
                                         campaigns = [simple_campaign],
                                         adgroups = [simple_adgroup],
                                         creatives = [simple_creative1, simple_creative2])
        
        basic_obj = simple_auc.to_basic_dict()
        new_simple_auc = from_basic_type(basic_obj)

        eq_(simple_auc, new_simple_auc)

