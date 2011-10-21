import random
import urllib, urllib2

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

class MarketplaceStatsFetcher(object):
    def __init__(self, app_keys = None, adunit_keys = None, account_keys = None):
        if not app_keys or adunit_keys or account_keys:
            raise Exception("Fuck you, pass in something")

        self.app_keys = app_keys
        self.adunit_keys = adunit_keys
        self.account_keys = account_keys

    def fetch(self):
            # payload = urllib2.urlopen('blah').read()
        payload = {}

        self.payload = payload

    def get_app_stats(self, app_key):
        return {
            "revenue": random.randint(1, 900),
            "impressions": random.randint(1, 10000),
            "clicks": random.randint(1, 1000),
        }

    def get_adunit_stats(self, adunit_key):
        return {
            "revenue": random.randint(1, 100),
            "impressions": random.randint(1, 10000),
            "clicks": random.randint(1, 1000),
        }

    def get_account_stats(self, account_key):
        return {
            "revenue": random.randint(1, 10000),
            "impressions": random.randint(1, 100000),
            "clicks": random.randint(1, 1000),
        }


    def get_all_dsp_stats(self, start, end):
        return {}

    def get_dsp_stats(self, dsp_name, start, end):
        return {}

    def get_top_creatives(self, limit=None):
        if limit = None:
            limit = 3

        return {}

    def get_creatives_for_dsp(self, dsp, start, end):
        return {}




def get_width_and_height(adunit):
    if adunit.format == "full" and not adunit.landscape:
        adunit_width = 320
        adunit_height = 480
    elif adunit.format == "full" and adunit.landscape:
        adunit_width = 480
        adunit_height = 320
    elif adunit.format == "full_tablet" and not adunit.landscape:
        adunit_width = 768
        adunit_height = 1024
    elif adunit.format == "full_tablet" and adunit.landscape:
        adunit_width = 1024
        adunit_height = 768
    else:
        adunit_width = adunit.get_width()
        adunit_height = adunit.get_height()
    return adunit_width, adunit_height