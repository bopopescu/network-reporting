import unittest
import sys
import os
PWD = os.path.dirname(__file__)
sys.path.append(os.path.join(PWD, '..'))


from interaction.account import AccountInteractionTestCase
from interaction.networks import NetworkInteractionTestCase
from interaction.marketplace import MarketplaceInteractionTestCase
from interaction.campaigns import DirectSoldInteractionTestCase
from interaction.inventory import InventoryInteractionTestCase

if __name__ == "__main__":
    unittest.main()
