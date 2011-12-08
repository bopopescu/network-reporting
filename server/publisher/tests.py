"""
Interaction tests for the mopub front-end. Interaction tests
use a live browser to test user actions like clicks, entering
and changing data, and navigation.

The tests in this module use selenium (http://seleniumhq.org/)
and assume a running selenium server on localhost. You'll also
have to have firefox installed.
"""

import unittest
import random
from selenium import webdriver
from time import sleep
BROWSER = None

class InteractionTestCase(unittest.TestCase):
    """
    Inheritable base class for testing interaction using selenium.
    Connects to a local selenium server instance before running
    any tests. Provides some common utility methods (login, logout)
    that are used in most browser tests.
    """

    def setUp(self):
        global BROWSER
        if BROWSER == None:
            BROWSER = webdriver.Firefox()
            # wait 10 seconds for each page to load
            BROWSER.implicitly_wait(10)

    def get(self, link):
        page = BROWSER.get("http://localhost:8000" + link)
        return page

    def login(self):
        self.get("/account/login/")
        email_field = BROWSER.find_element_by_name('username')
        email_field.send_keys("test@example.com")
        password_field = BROWSER.find_element_by_name('password')
        password_field.send_keys("test")
        login_button = BROWSER.find_element_by_id("accountForm-submit")
        login_button.click()

    def logout(self):
        self.get('/')
        try:
            logout_button = BROWSER.find_element_by_id("logout-link")
            logout_button.click()
        except:
            pass


class AccountInteractionTestCase(InteractionTestCase):
    """
    Selenium tests for the account and registration apps, as
    well as for the sign up process.
    """
    def testRegisterAccount(self):
        """
        Tests the creation of a new account (uses random variables).
        Doesn't test the whole sign up process, just the actual
        registration part.
        """
        self.logout()
        self.get('/account/login/')
        register_link = BROWSER.find_element_by_id("register-account")
        register_link.click()
        email_field = BROWSER.find_element_by_id("id_email")
        password_field = BROWSER.find_element_by_id("id_password1")
        password_again_field = BROWSER.find_element_by_id("id_password2")
        first_name_field = BROWSER.find_element_by_id("id_first_name")
        last_name_field = BROWSER.find_element_by_id("id_last_name")
        company_field = BROWSER.find_element_by_id("id_company")
        tos_button = BROWSER.find_element_by_id("id_tos")

        test_email = "test" + str(random.randint(1,100)) + "@example.mopub.com"
        email_field.send_keys(test_email)
        password_field.send_keys("test")
        password_again_field.send_keys("test")
        first_name_field.send_keys("Test")
        last_name_field.send_keys("Tester")
        company_field.send_keys("Selenium Test")
        tos_button.click()

        continue_button = BROWSER.find_element_by_id("accountForm-submit")
        continue_button.click()


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
        # self.login()
        # driver.wait_for_page_to_load(30000)
        # driver.open('/inventory')
        # driver.wait_for_page_to_load(30000)
        # page_title = driver.get_text("xpath=//div[@id='titlebar']//h1")
        # self.assertEqual(page_title, "Dashboard")
        # driver.capture_entire_page_screenshot('~/Desktop/selenium.png', {})
        pass

    def testGeoPerformance(self):
        """
        Navigate to the geo performance page and make sure it loads.
        """
        # self.login()
        # driver.wait_for_page_to_load(30000)
        # driver.open('/inventory')
        # driver.wait_for_page_to_load(30000)
        # driver.click("link=/inventory/geo")
        # driver.wait_for_page_to_load(30000)
        # page_title = driver.get_text("xpath=//div[@id='titlebar']//h1")
        # self.assertEqual(page_title, "Region Performance")
        pass

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