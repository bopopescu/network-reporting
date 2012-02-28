from interaction_tests.core import InteractionTestCase

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

