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
    def __init__(self, account_keys):
        self.account_keys = account_keys
        self.payload = {}

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
        stats = {
            "1": {
                "url": "http://www.google.com/",
                "name": "AdBlah",
                "stats": {
                    "chrg": 100,
                    "imp": 53082,
                    "bid": 31093,
                    "pub_rev": 4520.13,
                    "bid_cnt": 29992,
                    "clk": 2942
                }
            },
            "2": {
                "url": "http://www.blobmob.com/",
                "name": "BlobMob",
                "stats": {
                    "chrg": 430,
                    "imp": 78282,
                    "bid": 99793,
                    "pub_rev": 9520.13,
                    "bid_cnt": 87992,
                    "clk": 9042
                }
            }
        }
        return stats

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