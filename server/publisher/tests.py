"""
Interaction tests for the mopub front-end. Interaction tests
use a live browser to test user actions like clicks, entering
and changing data, and navigation.

The tests in this module use selenium (http://seleniumhq.org/)
and assume a running selenium server on localhost. You'll also
have to have firefox installed.
"""

import unittest
from selenium import selenium

class InteractionTestCase(unittest.TestCase):
    """
    Inheritable base class for testing interaction using selenium.
    Connects to a local selenium server instance before running
    any tests. Provides some common utility methods (login, logout)
    that are used in most browser tests.
    """
    def setUp(self):
        # TODO: make this work on endpoints other than localhost.
        self.selenium = selenium("localhost",
                                 4444,
                                 "*firefox",
                                 "http://localhost:8000/")
        self.selenium.start()

    def tearDown(self):
        self.selenium.close()

    def login(self):
        s = self.selenium
        s.open("/account/login/")
        s.type('name=username', "test@example.com")
        s.type('name=password', "test")
        s.click('id=accountForm-submit')

    def logout(self):
        s = self.selenium
        s.click('id=logout-link')



class AccountInteractionTestCase(InteractionTestCase):
    """
    Selenium tests for the account and registration apps, as
    well as for the sign up process.
    """
    def testCreateNewAccount(self):
        """
        Tests the creation of a new account (uses random variables).
        Doesn't test the whole sign up process, just the actual
        registration part.
        """
        s = self.selenium
        self.logout()
        s.wait_for_page_to_load(30000)
        s.open('/')
        s.wait_for_page_to_load(30000)
        s.click("id=register-account")
        s.wait_for_page_to_load(30000)

    def testSignUpProcess(self):
        """
        Goes through the entire sign up process (registration, create an app,
        create an adunit).
        """
        pass


class DirectSoldInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the direct sold dashboard and direct-sold campaign forms.
    """

    def testCampaignsLoad(self):
        """
        Makes sure the direct sold campaigns page can load.
        """
        pass

    def testFilterByRunning(self):
        """
        """
        pass

    def testFilterByScheduled(self):
        """
        """
        pass

    def testFilterByPaused(self):
        """
        """
        pass

    def testFilterByApp(self):
        """
        """
        pass

    def testAddGuaranteedCampaign(self):
        """
        """
        pass

    def testAddPromoCampaign(self):
        """
        """
        pass

    def testAddBackfillPromoCampaign(self):
        """
        """
        pass

    def testCampaignDetail(self):
        """
        """
        pass

    def testEditCampaign(self):
        """
        """
        pass


class MarketplaceInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the marketplace dashboard and marketplace settings.
    """

    def testMarketplaceLoad(self):
        """
        Makes sure the marketplace page can load.
        """
        pass

    def testChangePriceFloor(self):
        """
        Changes the price floor for an app and refreshes the page,
        making sure the price floor was changed.
        """
        pass

    def testChangeEnabled(self):
        """
        Changes the enabled-ness of a marketplace adunit and refreshes
        the page, making sure the enabling was changed.
        """
        pass

    def testTurnMarketplaceOff(self):
        """
        """
        pass

    def testTurnMarketplaceOn(self):
        """
        """
        pass

    def testTurnBlindnessOn(self):
        """
        """
        pass

    def testTurnBlindnessOff(self):
        """
        """
        pass

    def testAddToBlocklist(self):
        """
        """
        pass

    def testRemoveFromBlocklist(self):
        """
        """
        pass


class NetworkInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the ad networks dashboard
    """

    def testNetworksLoad(self):
        """
        """
        pass

    def testAddNewNetwork(self):
        """
        """
        pass

    def testAddNewNetworkWithAdvancedTargeting(self):
        """
        """
        pass

    def testEditNetwork(self):
        """
        """
        pass

    def testPauseNetwork(self):
        """
        """
        pass

    def testResumeNetwork(self):
        """
        """
        pass

    def testDeleteNetwork(self):
        """
        """
        pass


class PublisherInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the app inventory dashboard, app detail page, adunit
    detail page,

    """

    def testInventoryLoad(self):
        """
        Navigate to the inventory page and make sure it loads.
        """
        s = self.selenium
        self.login()
        s.wait_for_page_to_load(30000)
        s.open('/inventory')
        s.wait_for_page_to_load(30000)
        page_title = s.get_text("xpath=//div[@id='titlebar']//h1")
        self.assertEqual(page_title, "Dashboard")

    def testGeoPerformance(self):
        """
        Navigate to the geo performance page and make sure it loads.
        """
        s = self.selenium
        self.login()
        s.wait_for_page_to_load(30000)
        s.open('/inventory/')
        s.wait_for_page_to_load(30000)
        s.click("link=/inventory/geo")
        s.wait_for_page_to_load(30000)
        page_title = s.get_text("xpath=//div[@id='titlebar']//h1")
        self.assertEqual(page_title, "Region Performance")

    def testAppDetailLoad(self):
        """
        """
        pass

    def testAppDetailLoad(self):
        """
        """
        pass

    def testCreateNewApp(self):
        """
        """
        pass

    def testCreateNewAdUnit(self):
        """
        """
        pass

    def testEditExistingApp(self):
        """
        """
        pass

    def testEditExistingAdUnit(self):
        """
        """
        pass

if __name__ == '__main__':
    unittest.main()