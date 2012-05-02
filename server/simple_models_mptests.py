########## Set up Django ###########
import sys
import os
import datetime
import copy
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
from google.appengine.ext import testbed

from account.models import *
from advertiser.models import *
from publisher.models import *




class TestBudgetEndToEnd(unittest.TestCase):


    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.net_cfg = NetworkConfig(admob_pub_id='1234',
                                     adsense_pub_id='derp_derp_derp',
                                     brightroll_pub_id='lookitmeimroolllinnggsobright',
                                     chartboost_pub_id='WHREYOUATchartBOOSTMOBILE',
                                     ejam_pub_id='ejamsoundslikeinternetjelly',
                                     greystripe_pub_id='fruitstripe>>greystripe',
                                     inmobi_pub_id='indiaaaaaaaaaaaa',
                                     jumptap_pub_id='new_basketball_workout',
                                     millenial_pub_id='LOOKATMEIMAPUBLICCOMPANY',
                                     mobfox_pub_id='foxesareprettycool',
                                     rev_share=.01,
                                     price_floor=1.0,
                                     )
        self.net_cfg.put()

        self.acct = Account(company='BestCompany',
                            domain='boobs',
                            network_config=self.net_cfg,
                            adsense_company_name='google.BestCompany',
                            adsense_test_mode=True)
        self.acct.put()

        self.app = App(account=self.acct,
                       name='MCDERP',
                       global_id='earth',
                       adsense_app_name='google.MCDERP',
                       adsense_app_id='fake_id',
                       admob_textcolor='0x323423',
                       admob_bgcolor='0x1231231',
                       app_type='iphone',
                       package='derp.derp.derp',
                       url='www.mcderp.com',
                       experimental_fraction=0.01,
                       network_config=self.net_cfg,
                       primary_category=u'sports',
                       secondary_category=u'travel',
                       force_marketplace=False)
        self.app.put()

        self.au = AdUnit(name='MCDERPUNIT',
                         account=self.acct,
                         app_key=self.app,
                         keywords='truck AND bannana',
                         format='728x90',
                         landscape=True,
                         custom_height=728,
                         custom_width=90,
                         adsense_channel_id='WDERPDR',
                         ad_type='image',
                         refresh_interval=75,
                         network_config=self.net_cfg,
                         )
        self.au.put()

        start= datetime.datetime(2000,1,1,1,1)
        end = datetime.datetime(2000,2,2,2,2,2)

        self.camp = Campaign(name='MEGACAMPAIGN',
                             campaign_type='network',
                             active=True,
                             start_datetime=start,
                             end_datetime=end,
                             account=self.acct,
                             full_budget=10000.,
                             budget_type='full_campaign')
        self.camp.put()

        self.ag = AdGroup(name='MCADGROUP',
                          campaign=self.camp,
                          account=self.acct,
                          bid=1.0,
                          bid_strategy='cpm',
                          active=True,
                          minute_frequency_cap=3,
                          hourly_frequency_cap=5,
                          daily_frequency_cap=10,
                          weekly_frequency_cap=15,
                          monthly_frequency_cap=20,
                          lifetime_frequency_cap=1,
                          keywords='a AND b',
                          site_keys=[self.au.key()],
                          mktplace_price_floor=10.0,
                          device_targeting=True,
                          target_iphone=True,
                          target_ipod=False,
                          target_ipad=True,
                          ios_version_max='4.0',
                          ios_version_min='3.2',
                          target_android=True,
                          android_version_max='1.5',
                          android_version_min='1.0'
                          target_other=True,
                          cities=['freeland','mexicaliwest'],
                          allocation_percentage=88.8,
                          optimizable=True,
                          default_cpm=3.6,
                          network_type='admob',
                          )
        self.ag.put()

        default_crtv_args = dict(active=True,
                                 name='unoriginal',
                                 custom_width=728,
                                 custom_heigt=100,
                                 landsacpe=True,
                                 ad_group=self.ag,
                                 ad_type='text',
                                 tracking_url='maps.google.com',
                                 url='www.lemonparty.com',
                                 display_url='www.www.google',
                                 conv_appid='mcderp',
                                 format='728x90',
                                 launchpage='www.wwwwwwwwwwwww')

        self.crtv1 = Creative(active=True,




    def mptest_basic_wrapping(self):
        pass

    def mptest_adding_random_params(self):
        pass


    def mptest_basic_type_conversion(self):
        """ this test effectively doesn't test shit """
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

