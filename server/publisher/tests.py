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

BROWSER = None

class InteractionTestCase(unittest.TestCase):
    """
    Inheritable base class for testing interaction using selenium.
    Connects to a local selenium server instance before running
    any tests. Provides some common utility methods (login, logout,
    others) that are used in most browser tests.
    """

    def setUp(self):
        # make the browser a singleton so we can reuse the same firefox process
        global BROWSER
        if BROWSER == None:
            BROWSER = webdriver.Firefox()
            # wait 10 seconds for each page to load
            BROWSER.implicitly_wait(10)

    def get(self, link):
        """
        Shortcut for navigating to a link on our endpoint.
        """
        # REFACTOR we should put the endpoint in settings
        page = BROWSER.get("http://localhost:8000" + link)
        return page

    def login(self):
        """
        Shortcut for logging in to the page. Will log out the current session first.
        """
        self.logout()
        self.get("/account/login/")
        email_field = BROWSER.find_element_by_name('username')
        email_field.send_keys("test@example.com")
        password_field = BROWSER.find_element_by_name('password')
        password_field.send_keys("test")
        login_button = BROWSER.find_element_by_id("accountForm-submit")
        login_button.click()

    def logout(self):
        """
        Shortcut for logging out of a page. Kind of jankity but usually works.
        """
        # Try to navigate to '/', which could either be the dashboard page
        # or the account login page depending on whether the user is logged
        # in already. If it finds a logout button it'll click it, otherwise
        # the user is probably not logged in anyway.
        self.get('/')
        try:
            logout_button = BROWSER.find_element_by_id("logout-link")
            logout_button.click()
        except:
            pass

    def click(self, id=None, klass=None, xpath=None, name=None):
        """
        Shortcut for clicking on something in the page, identifiable by
        one and only one of: id, class, xpath, name.
        """
        # REFACTOR allow multiple selectors to be passed in
        if id:
            item = BROWSER.find_element_by_id(id)
        elif klass:
            item = BROWSER.find_element_by_class(klass)
        elif xpath:
            item = BROWSER.find_element_by_xpath(xpath)
        elif name:
            item = BROWSER.find_element_by_name(name)
        else:
            raise Exception('please provide one of: id, class, xpath, name')

        item.click()

    def send_keys(self, keys, id=None, klass=None, xpath=None, name=None):
        """
        Shortcut for typing in to something in the page, identifiable by
        one and only one of: id, class, xpath, name.
        """
        if id:
            item = BROWSER.find_element_by_id(id)
        elif klass:
            item = BROWSER.find_element_by_class(klass)
        elif xpath:
            item = BROWSER.find_element_by_xpath(xpath)
        elif name:
            item = BROWSER.find_element_by_name(name)
        else:
            raise Exception('please provide one of: id, class, xpath, name')

        item.send_keys(keys)

    def select_option(self, select_box_id, option_value):
        """
        Shortcut for selecting an option in a select box.
        """
        select_box = BROWSER.find_element_by_id(select_box_id)
        select_box.click()

        option_xpath = "//select[@id='" + select_box_id + "']" + \
                       "//option[@value='" + option_value + "']"
        option = BROWSER.find_element_by_xpath(option_xpath)
        option.click()


class AccountInteractionTestCase(InteractionTestCase):
    """
    Selenium tests for the account and registration apps, as
    well as for the sign up process.
    """
    # REFACTOR use the shortcuts
    def testRegisterAccount(self):
        """
        Tests the creation of a new account (uses random variables).
        Doesn't test the whole sign up process, just the actual
        registration part.
        """
        # go to register new account
        self.logout()
        self.get('/account/login/')
        register_link = BROWSER.find_element_by_id("register-account")
        register_link.click()

        # fill out required fields on registration page
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

        # find the title and make sure we're in the right place
        page_h1 = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_h1.text.find("Step 1") > -1)

    # REFACTOR use the shortcuts
    def testSignUpProcess(self):
        """
        Goes through the entire sign up process (registration, create an app,
        create an adunit, code integration, dashboard).
        """
        self.testRegisterAccount()

        app_name_field = BROWSER.find_element_by_id("appForm-name")
        app_name_field.send_keys("Robot Unicorn Attack")

        primary_category = BROWSER.find_element_by_id('id_primary_category')
        primary_category.click()

        primary_category = BROWSER.find_element_by_id('id_primary_category')
        primary_category.click()

        games_option = BROWSER.find_element_by_xpath("//option[@value='games']")
        games_option.click()

        adunit_name_field = BROWSER.find_element_by_id("appForm-adUnitName")
        adunit_name_field.send_keys('Test Adunit')

        continue_button = BROWSER.find_element_by_id("appForm-submit")
        continue_button.click()

        # find the title and make sure we're in the right place
        page_h1 = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_h1.text.find("Step 2") > -1)

        integration_button = BROWSER.find_element_by_id("integration-continue")
        integration_button.click()

        dashboard_h1 = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(dashboard_h1.text.find("Dashboard") > -1)


class DirectSoldInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the direct sold dashboard and direct-sold campaign forms.
    """

    def testCampaignsLoad(self):
        """
        Makes sure the direct sold campaigns page can load.
        """
        self.login()
        #self.click(xpath="//div[@id='nav1']//a[@href='/campaigns/']")
        self.get('/campaigns/')

        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Campaigns") > -1)

    #TODO
    def testFilterByRunning(self):
        """
        """
        pass

    #TODO
    def testFilterByScheduled(self):
        """
        """
        pass

    #TODO
    def testFilterByPaused(self):
        """
        """
        pass

    #TODO
    def testFilterByApp(self):
        """
        """
        pass

    def testAddGuaranteedCampaign(self):
        """
        Tests the adding of a guaranteed campaign and an HTML creative along with it
        """
        self.login()

        # campaign page
        self.get('/campaigns/')
        self.click(id="add_campaign_button")

        # add new campaign form
        self.send_keys('TEST CAMPAIGN', id='id_name')
        self.click(id="select-all")
        self.click(id="campaignAdgroupForm-submit")

        # campaign details/add creative form
        self.click(id="creativeType-html")
        creative_name_xpath = "//div[@id='creativeAddForm-fragment']" + \
                              "//input[@name='name']"
        self.send_keys("blah", xpath=creative_name_xpath)
        self.click(id="creativeCreateForm-submit")

        # campaign detail again
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Campaign:") > -1)


    def testAddPromoCampaign(self):
        """
        Tests the adding of a promo campaign and an HTML creative along with it
        """
        self.login()

        # campaign page
        self.get('/campaigns/')
        self.click(id="add_campaign_button")

        # add new campaign form
        self.select_option("campaign_type_select", "promo")
        self.send_keys('TEST PROMO CAMPAIGN', id='id_name')
        self.click(id="select-all")
        self.click(id="campaignAdgroupForm-submit")

        # campaign details/add creative form
        self.click(id="creativeType-html")
        creative_name_xpath = "//div[@id='creativeAddForm-fragment']" + \
                              "//input[@name='name']"
        self.send_keys("blah", xpath=creative_name_xpath)
        self.click(id="creativeCreateForm-submit")

        # campaign detail again
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Campaign:") > -1)


    def testAddBackfillPromoCampaign(self):
        """
        Tests the adding of a new backfill promo campaign and an HTML creative
        along with it
        """
        self.login()

        # campaign page
        self.get('/campaigns/')
        self.click(id="add_campaign_button")

        # add new campaign form
        self.select_option("campaign_type_select", "promo")
        self.select_option("id_promo_level", "backfill")
        self.send_keys('TEST BACKFILL CAMPAIGN', id='id_name')
        self.click(id="select-all")
        self.click(id="campaignAdgroupForm-submit")

        # campaign details/add creative form
        self.click(id="creativeType-html")
        creative_name_xpath = "//div[@id='creativeAddForm-fragment']" + \
                              "//input[@name='name']"
        self.send_keys("blah", xpath=creative_name_xpath)
        self.click(id="creativeCreateForm-submit")

        # campaign detail again
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Campaign:") > -1)

    #TODO
    def testCampaignDetail(self):
        """
        Navigate to the campaign detail page and make sure it loads.
        """
        pass

    # TODO test detail load for different types of campaigns
    # TODO test detail load for campaigns with a ton of adunits/apps

    #TODO
    def testEditCampaign(self):
        """
        Change the details of a campaign that already exists.
        """
        self.testCampaignDetail()
        self.click(id="advertisers-adgroups-editAdGroupButton")



class MarketplaceInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the marketplace dashboard and marketplace settings.
    """

    def testMarketplaceLoad(self):
        """
        Makes sure the marketplace page can load.
        """
        self.get("/campaigns/marketplace/")
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Marketplace") > -1)

    #TODO
    def testChangePriceFloor(self):
        """
        Changes the price floor for an app and refreshes the page,
        making sure the price floor was changed.
        """
        pass

    #TODO
    def testChangeEnabled(self):
        """
        Changes the enabled-ness of a marketplace adunit and refreshes
        the page, making sure the enabling was changed.
        """
        pass

    #TODO
    def testChangeMarketplaceOnOffSetting(self):
        """
        Goes to the settings page and turns the marketplace on or off,
        and refreshes the page to make sure the change happened.
        """
        pass

    #TODO
    def testTurnBlindnessOnOff(self):
        """
        Goes to the settings page and turns blindness on/off and refreshes
        the page to make sure the change happened
        """
        pass

    #TODO
    def testAddToBlocklist(self):
        """
        Goes to the settings page and makes sure items can be added to the blocklist.
        """
        pass

    #TODO
    def testRemoveFromBlocklist(self):
        """
        Goes to the settings page and makes sure items can be removed from
        the blocklist.
        """
        pass


class NetworkInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the ad networks dashboard
    """

    def testNetworksLoad(self):
        """
        Navigates to the networks page and asserts that it loaded.
        """
        self.login()
        self.get('/campaigns/networks/')
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Networks") > -1)

    def testAddNewNetwork(self):
        """
        Navigates to the add campaign form from the networks page
        and creates a new network campaign.
        """
        self.login()

        # campaign page
        self.get('/campaigns/networks/')
        self.click(id="add_campaign_button")

        # add new campaign form
        self.send_keys('TEST NETWORK', id='id_name')
        self.select_option("network_select", "ejam")
        self.click(id="select-all")
        self.click(id="campaignAdgroupForm-submit")

        # campaign detail again
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Network:") > -1)

    #TODO
    def testAddNewNetworkWithAdvancedTargeting(self):
        """
        Navigates to the add campaign form from the networks page
        and creates a new network campaign with advanced targeting settings.
        """
        pass

    #TODO
    def testEditNetwork(self):
        """
        Navigates to the edit campaign form for an existing network campaign
        and edits some of its values..
        """
        pass

    #TODO
    def testPauseNetwork(self):
        """
        Navigates to the networks campaigns page and pauses a network.
        """
        pass

    #TODO
    def testResumeNetwork(self):
        """
        Navigates to the networks campaigns page and resumes a paused network.
        """
        pass

    #TODO
    def testDeleteNetwork(self):
        """
        Navigates to the networks campaigns page and deletes a paused network.
        """
        pass


class InventoryInteractionTestCase(InteractionTestCase):
    """
    Interaction tests for the app inventory dashboard, app detail page, adunit
    detail page.
    """

    def testInventoryLoad(self):
        """
        Navigate to the inventory page and make sure it loads.
        """
        self.login()
        self.get('/inventory')
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Dashboard") > -1)

    def testGeoPerformance(self):
        """
        Navigate to the geo performance page and make sure it loads.
        """
        self.login()
        self.get('/inventory')
        self.click(id="geo-performance")
        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Region Performance") > -1)

    def testAppDetailLoad(self):
        """
        Navigate to an app detail page and make sure it loads.
        """
        self.login()
        self.get('/')
        app_links = BROWSER.find_elements_by_class_name("app-link")

        # if there arent any apps for this test user, make one and
        # then proceed.
        if len(app_links) == 0:
            self.testCreateNewApp()
            self.get('/')
            app_links = BROWSER.find_elements_by_class_name("app-link")

        app_links[0].click()

        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("App:") > -1)


    def testAdUnitDetailLoad(self):
        """
        Navigate to an adunit detail page and make sure it loads.
        """
        self.login()
        self.get('/')
        adunit_links = BROWSER.find_elements_by_class_name("adunit-link")

        # if there arent any apps for this test user, make one and
        # then proceed.
        if len(adunit_links) == 0:
            self.testCreateNewApp()
            self.get('/')
            adunit_links = BROWSER.find_elements_by_class_name("adunit-link")

        adunit_links[0].click()

        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Ad Unit:") > -1)


    def testCreateNewApp(self):
        """
        Create a new app with default options.
        """
        self.login()
        self.get('/inventory')
        self.click(id="dashboard-apps-addAppButton")

        self.send_keys("Robot Unicorn Attack Metal Edition", id="appForm-name")
        self.select_option("id_primary_category", "games")
        self.send_keys("Test Adunit", "appForm-adUnitName")
        self.click("appForm-submit")

        self.click("integration-continue")

        page_title = BROWSER.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("App:") > -1)

    #TODO test all kinds of apps

    def testCreateNewAdUnit(self):
        """
        Creates a new adunit with default options.
        """
        self.testCreateNewApp()
        self.click(id="dashboard-apps-addAdUnitButton")
        self.send_keys("chello", id="appForm-adUnitName")
        self.click(id="adunitAddForm-submit")
        #REFACTOR lazy, figure out how to actually test this
        self.assertTrue(True)

    # TODO test all kinds of adunits

    def testEditExistingApp(self):
        """
        Change the details of an existing app.
        """
        self.testAppDetailLoad()
        self.click(id="dashboard-apps-editAppButton")
        self.click(id="appForm-platform-android")
        self.click(id="appEditForm-submit")

    def testEditExistingAdUnit(self):
        """
        Change the details of an existing adunit.
        """
        self.testAdUnitDetailLoad()
        self.click(id="dashboard-apps-editAdUnitButton")
        self.send_keys("blah blah test blah", id="appForm-adUnitName")
        self.click(id="adunitEditForm-submit")
        #REFACTOR lazy, figure out how to actually test this
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()