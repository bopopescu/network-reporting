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


from google.appengine.ext import testbed
for a in sys.modules:
    if 'advertiser' in a.lower():
        logging.warning("Modules: %s, value: %s" % (a, sys.modules[a]))
logging.warning("trying to import campaign")
from advertiser.models import (Campaign,
                               AdGroup,
                               Creative,
                               HtmlCreative,
                               TextCreative,
                               TextAndTileCreative,
                               ImageCreative,
                               MarketplaceCreative,
                               CustomCreative,
                               CustomNativeCreative,
                               iAdCreative,
                               AdSenseCreative,
                               AdMobCreative,
                               AdMobNativeCreative,
                               MillennialCreative,
                               MillennialNativeCreative,
                               ChartBoostCreative,
                               EjamCreative,
                               InMobiCreative,
                               AppNexusCreative,
                               BrightRollCreative,
                               JumptapCreative,
                               GreyStripeCreative,
                               MobFoxCreative,
                               )
from publisher.models import App, AdUnit
from account.models import Account, NetworkConfig
from ad_server.adunit_context.adunit_context import AdUnitContext


from simple_models import (SimpleAccount,
                           SimpleAdUnit,
                           SimpleCampaign,
                           SimpleAdGroup,
                           SimpleCreative,
                           SimpleAdUnitContext,
                           from_basic_type)

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
                       secondary_category=u'travel')
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
                          keywords=['a','b'],
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
                          android_version_min='1.0',
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
                                 launchpage='www.wwwwwwwwwwwww',
                                 )

        self.crtv1 = Creative(**default_crtv_args)
        self.crtv1.put()

        text_args = copy.copy(default_crtv_args)
        text_args['headline'] = 'HEARYEHEARYE'
        text_args['line1'] = 'NICKWINS5MILLIONDOLLARLOTTERY'
        text_args['line2'] = 'SPENDSITALLONUGLYHOOKERS'

        self.crtv2 = TextCreative(**text_args)
        self.crtv2.put()
        textandtile_args = copy.copy(default_crtv_args)
        dict2 = dict(line1='TURNSOUTUGLYHOOKERSAREACTUALLYPETERSMOM',
                     line2='STILL,GROSSLYOVERPAID',
                     image_url='www.ugly.jpg',
                     action_icon='download_arrow4',
                     color='00000',
                     font_color='4f3fff',
                     gradient=True,
                     )
        textandtile_args.update(dict2)
        self.crtv3 = TextAndTileCreative(**textandtile_args)
        self.crtv3.put()

        self.crtv4=HtmlCreative(html_data='<html>LOOKITERNETS</html>',
                                ormma_html=False,
                                **default_crtv_args)
        self.crtv4.put()
        self.crtv5=ImageCreative(image_url='derpyderpy',
                                 **default_crtv_args
                                 )
        self.crtv5.put()
        self.crtv6 = MarketplaceCreative(**default_crtv_args)
        self.crtv6.put()
        self.crtv7 = CustomCreative(**default_crtv_args)
        self.crtv7.put()
        self.crtv8 = CustomNativeCreative(**default_crtv_args)
        self.crtv8.put()
        self.c9 = iAdCreative(**default_crtv_args)
        self.c9.put()
        self.c10 = AdSenseCreative(**default_crtv_args)
        self.c10.put()
        self.c11 = AdMobCreative(**default_crtv_args)
        self.c11.put()
        self.c12 = AdMobNativeCreative(**default_crtv_args)
        self.c12.put()
        self.c13 = MillennialCreative(**default_crtv_args)
        self.c13.put()
        self.c14 = MillennialNativeCreative(**default_crtv_args)
        self.c14.put()
        self.c15 = ChartBoostCreative(**default_crtv_args)
        self.c15.put()
        self.c16 = EjamCreative(**default_crtv_args)
        self.c16.put()
        self.c17 = InMobiCreative(**default_crtv_args)
        self.c17.put()
        self.c18 = AppNexusCreative(**default_crtv_args)
        self.c18.put()
        self.c19 = BrightRollCreative(**default_crtv_args)
        self.c19.put()
        self.c20 = JumptapCreative(**default_crtv_args)
        self.c20.put()
        self.c21 = GreyStripeCreative(**default_crtv_args)
        self.c21.put()
        self.c22 = MobFoxCreative(**default_crtv_args)
        self.c22.put()

        self.auc = AdUnitContext.wrap(self.au)



    def mptest_basic_wrapping(self):
        simple = self.auc.simplify()
        basic = simple.to_basic_dict()
        print simple
        print from_basic_type(basic)
        assert from_basic_type(basic) == simple

    def mptest_adding_random_params(self):
        for c in self.auc.creatives:
            c.random_property = 'derpaderp'
            c.magic = 'WOOOOOO'
        simple = self.auc.simplify()
        assert simple is not None
        for c in simple.creatives:
            assert getattr(c, 'random_property', None) is None
            assert getattr(c, 'magic', None) is None
        for c in self.auc.creatives:
            assert getattr(c, 'random_property', None) is not None
            assert getattr(c, 'magic', None) is not None

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

    def mptest_geo_predicates(self):
        """
        Test that we don't let 'country=' get passed to ad_server
        because things break.
        """
        self.ag.geo_predicates = ['country=']
        simple_adgroup = self.ag.simplify()
        eq_(simple_adgroup.geo_predicates, ['country=*'])
