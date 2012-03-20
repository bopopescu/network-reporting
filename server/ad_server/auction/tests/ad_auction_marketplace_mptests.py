########## Set up Django ###########
import sys
import os
import datetime
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from account.models import Account

from publisher.models import App
from publisher.models import Site as AdUnit

from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
                                )
from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )

from ad_server.main import  ( AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )
from ad_server.handlers import adhandler
from ad_server.handlers.adhandler import AdHandler
from ad_server.optimizer import optimizer

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
############# Integration Tests #############
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from budget.models import (Budget,
                           BudgetSliceLog,
                           )
from google.appengine.api import memcache


from advertiser.models import (DummyServerSideSuccessCreative,
                               DummyServerSideFailureCreative,
                               MarketplaceCreative,
                              )

from ad_server.auction.client_context import ClientContext

from ad_server.auction import ad_auction
from google.appengine.ext import testbed
################# End to End #################

from ad_server.auction.battles import (Battle,
                                       GteeBattle,
                                       GteeHighBattle,
                                       GteeLowBattle,
                                       MarketplaceBattle,
                                      )

class DummyMarketplaceBattle(MarketplaceBattle):
    """ Like Marketplace but always returns a creative.
        For Testing purposes. """
    cpm_of_winning_bid = 0.50 # Arbitrary default value for testing

    def _process_winner(self, creative):
        """ return a creative with a default bid. """
        creative.adgroup.bid = self.cpm_of_winning_bid
        return creative

class TestAdAuction(unittest.TestCase):


    def setUp(self):
        """ We make three Campaigns:
                expensive_c - network with eCPM of 1.00, always fails
                cheap_c - network with eCPM of 0.25, always succeeds
                marketplace_c - always returns a bid with eCPM of 0.50

            All three target the same adgroup.
        """


        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()


        # Set up default models
        self.account = Account()
        self.account.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()

        self.adunit = AdUnit(account=self.account,
                                     app_key=self.app,
                                     name="Test AdUnit",
                                     format=u'320x50')
        self.adunit.put()

        ###################################
        # Make cheap campaign: worth 0.25
        self.cheap_c = Campaign(name="cheap",
                                campaign_type="network")
        self.cheap_c.put()

        self.cheap_adgroup = AdGroup(account=self.account,
                              name="cheap",
                              campaign=self.cheap_c,
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpm",
                              bid=0.25)
        self.cheap_adgroup.put()


        self.cheap_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.cheap_adgroup)
        self.cheap_creative.put()

        ###################################
        # Make marketplace campaign: worth 0.50 (default for dummy marketplace)

        self.dummy_marketplace_c = Campaign(name="dummy_network",
                                        campaign_type="marketplace")

        self.dummy_marketplace_c.put()

        self.dummy_marketplace_adgroup = AdGroup(account=self.account,
                              campaign=self.dummy_marketplace_c,
                              site_keys=[self.adunit.key()],
                              network_type="dummy") # dummy networks go to the DummyServerSide

        self.dummy_marketplace_adgroup.put()

        self.dummy_marketplace_creative = MarketplaceCreative(account=self.account,
                                ad_group=self.dummy_marketplace_adgroup)

        self.dummy_marketplace_creative.put()


    def tearDown(self):
        self.testbed.deactivate()

    def _make_expensive_creative_succeed(self):
        ###################################
        # Make expensive campaign: worth 1.00
        # Note that this campaign will always fail

        self.expensive_c = Campaign(name="expensive",
                                    campaign_type="network")
        self.expensive_c.put()

        self.expensive_adgroup = AdGroup(account=self.account,
                                          name="expensive",
                                          campaign=self.expensive_c,
                                          site_keys=[self.adunit.key()],
                                          bid_strategy="cpm",
                                          bid=1.00) # 100 per click
        self.expensive_adgroup.put()



        self.expensive_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.expensive_adgroup)
        self.expensive_creative.put()

        adunit_id = str(self.adunit.key())
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)

    def _make_expensive_creative_fail(self):
        ###################################
        # Make expensive campaign: worth 1.00
        # Note that this campaign will always fail

        self.expensive_c = Campaign(name="expensive",
                                    campaign_type="network")
        self.expensive_c.put()

        self.expensive_adgroup = AdGroup(account=self.account,
                                          name="expensive",
                                          campaign=self.expensive_c,
                                          site_keys=[self.adunit.key()],
                                          bid_strategy="cpm",
                                          bid=1.00) # 100 per click
        self.expensive_adgroup.put()



        self.expensive_creative = DummyServerSideFailureCreative(account=self.account,
                                ad_group=self.expensive_adgroup)
        self.expensive_creative.put()

        adunit_id = str(self.adunit.key())
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)

    def mptest_ecpms(self):
        """ Make sure that we actually have set ecpms for our networks apropriately """
        self._make_expensive_creative_fail()
        eq_(optimizer.get_ecpm(self.adunit, self.expensive_creative), 1.00)
        eq_(optimizer.get_ecpm(self.adunit, self.cheap_creative), 0.25)


    def mptest_marketplace_beating_failed_networks(self):
        """ If the best marketplace bid with .50, and there are two networks worth
            1.00 and .25, then if the 1.00 fails, go directly to the marketplace
            without pinging the crappier network. """
        self._make_expensive_creative_fail()
        client_context = ClientContext(adunit=self.adunit,
                                       keywords=None,
                                       country_code=None,
                                       excluded_adgroup_keys=[],
                                       raw_udid="FakeUDID",
                                       ll=None,
                                       request_id=None,
                                       now=datetime.datetime.now(),
                                       user_agent='FakeAndroidOS',
                                       experimental=False)
        # Unpack results
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context,
                                                            self.adunit_context,
                                                            MarketplaceBattle=DummyMarketplaceBattle)
        eq_obj(creative, self.dummy_marketplace_creative)

    def mptest_network_beating_marketplace(self):
        """ If a network with an ecpm higher than the best marketplace bid
            returns a valid creative, use it """

        self._make_expensive_creative_succeed()

        client_context = ClientContext(adunit=self.adunit,
                                       keywords=None,
                                       country_code=None,
                                       excluded_adgroup_keys=[],
                                       raw_udid="FakeUDID",
                                       ll=None,
                                       request_id=None,
                                       now=datetime.datetime.now(),
                                       user_agent='FakeAndroidOS',
                                       experimental=False)
        # Unpack results
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context,
                                                            self.adunit_context,
                                                            MarketplaceBattle=DummyMarketplaceBattle)

        eq_obj(creative, self.expensive_creative)



    def mptest_marketplace_beating_failed_networks_with_exclusion(self):
        """ If the best marketplace bid with .50, and there are two networks worth
            1.00 and .25, then if the 1.00 is excluded, go directly to the
            marketplace without pinging the crappier network. """

        self._make_expensive_creative_succeed()
        client_context = ClientContext(adunit=self.adunit,
                                       keywords=None,
                                       country_code=None,
                                       excluded_adgroup_keys=[str(self.expensive_adgroup.key())],
                                       raw_udid="FakeUDID",
                                       ll=None,
                                       request_id=None,
                                       now=datetime.datetime.now(),
                                       user_agent='FakeAndroidOS',
                                       experimental=False)
        # Unpack results
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context,
                                                            self.adunit_context,
                                                            MarketplaceBattle=DummyMarketplaceBattle)
        eq_obj(creative, self.dummy_marketplace_creative)


def eq_obj(obj1, obj2):
    eq_(obj1.key(), obj2.key())
