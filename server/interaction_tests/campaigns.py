from interaction_tests.core import InteractionTestCase

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

        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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
        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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
        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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
        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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


