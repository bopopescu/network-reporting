from interaction_tests.core import InteractionTestCase

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
        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Dashboard") > -1)

    def testGeoPerformance(self):
        """
        Navigate to the geo performance page and make sure it loads.
        """
        self.login()
        self.get('/inventory')
        self.click(id="geo-performance")
        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("Region Performance") > -1)

    def testAppDetailLoad(self):
        """
        Navigate to an app detail page and make sure it loads.
        """
        self.login()
        self.get('/')
        app_links = self.browser.find_elements_by_class_name("app-link")

        # if there arent any apps for this test user, make one and
        # then proceed.
        if len(app_links) == 0:
            self.testCreateNewApp()
            self.get('/')
            app_links = self.browser.find_elements_by_class_name("app-link")

        app_links[0].click()

        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
        self.assertTrue(page_title.text.find("App:") > -1)


    def testAdUnitDetailLoad(self):
        """
        Navigate to an adunit detail page and make sure it loads.
        """
        self.login()
        self.get('/')
        adunit_links = self.browser.find_elements_by_class_name("adunit-link")

        # if there arent any apps for this test user, make one and
        # then proceed.
        if len(adunit_links) == 0:
            self.testCreateNewApp()
            self.get('/')
            adunit_links = self.browser.find_elements_by_class_name("adunit-link")

        adunit_links[0].click()

        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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

        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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
