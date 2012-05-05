from interaction.core import InteractionTestCase

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
        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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
        page_title = self.browser.find_element_by_xpath("//div[@id='titlebar']//h1")
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
