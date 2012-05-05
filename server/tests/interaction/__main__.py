import unittest
import sys
import os
PWD = os.path.dirname(__file__)
sys.path.append(os.path.join(PWD, '..'))


from interaction_tests.account import AccountInteractionTestCase
from interaction_tests.networks import NetworkInteractionTestCase
from interaction_tests.marketplace import MarketplaceInteractionTestCase
from interaction_tests.campaigns import DirectSoldInteractionTestCase
from interaction_tests.inventory import InventoryInteractionTestCase

if __name__ == "__main__":
    unittest.main()
