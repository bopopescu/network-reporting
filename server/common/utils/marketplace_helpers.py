
import random
import urllib, urllib2

from common_templates.templatetags.filters import currency, percentage, percentage_rounded

import logging

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
        imp = random.randint(1, 100000)
        rev =  random.randint(1, 100000)
        clk = random.randint(1, imp/10)
        ctr = (clk/float(imp))
        ecpm = (rev/float(imp))*1000

        return {
            "revenue": rev,
            "impressions": imp,
            "clicks": clk,
            "ecpm": currency(ecpm),
            "ctr": percentage(ctr)
        }


    def get_adunit_stats(self, adunit_key):
        imp = random.randint(1, 100000)
        rev =  random.randint(1, 100000)
        clk = random.randint(1, imp/10)
        ctr = (clk/float(imp))
        ecpm = (rev/float(imp))*1000

        return {
            "revenue": rev,
            "impressions": imp,
            "clicks": clk,
            "ecpm": currency(ecpm),
            "ctr": percentage(ctr)
        }


    def get_account_stats(self, account_key):
        imp = random.randint(1, 100000)
        rev =  random.randint(1, 100000)
        clk = random.randint(1, imp/10)
        ctr = (clk/float(imp))
        ecpm = (rev/float(imp))*1000

        return {
            "revenue": rev,
            "impressions": imp,
            "clicks": clk,
            "ecpm": currency(ecpm),
            "ctr": percentage(ctr)
        }


    def get_all_dsp_stats(self, start, end):
        stats = {
            "DSP1": {
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
            "DSP2": {
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

        # Make the stats iterable so we can use them in a template
        i_stats = []
        for k, v in stats.iteritems():
            v['key'] = k
            i_stats.append(v)

        return i_stats

    def get_dsp_stats(self, dsp_key, start, end):
        stats = {
            "DSP1": {
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
            "DSP2": {
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

        dsp_stats = stats[dsp_key]

        # keys are often used for front-end handlers,
        # so return the key too
        dsp_stats['key'] = dsp_key

        return dsp_stats

    def get_creatives_for_dsp(self, dsp_key, start, end):
        creative_stats = {
            "DSP1": {
                'CREATIVE1': {
                    'stats': {
                        'chrg': 2340,
                        'imp': 23490,
                        'bid': 24902,
                        'bid_cnt': 2394,
                        'pub_rev': 2030,
                        'clk': 3012
                    },
                    'creative': {
                        'body': "blah bla",
                        '_id': "asdo2nOASINdlnasd",
                        'url': "http://www.profilebrand.com/graphics/category/animals/4904_pitbulls-are-great-dogs.png",
                        'dsp': "DSP1",
                        'crtv_id': "CREATIVE1"
                    }
                },
                'CREATIVE2': {
                    'stats': {
                        'chrg': 2340,
                        'imp': 23490,
                        'bid': 24902,
                        'bid_cnt': 2394,
                        'pub_rev': 2030,
                        'clk': 3012
                    },
                    'creative': {
                        'body': "blah bla",
                        '_id': "asdo2nOASINdlnasd",
                        'url': "http://www.profilebrand.com/graphics/category/animals/4904_pitbulls-are-great-dogs.png",
                        'dsp': "DSP1",
                        'crtv_id': "CREATIVE2"
                    }
                }
            },
            "DSP2": {
                'CREATIVE1': {
                    'stats': {
                        'chrg': 2340,
                        'imp': 23490,
                        'bid': 24902,
                        'bid_cnt': 2394,
                        'pub_rev': 2030,
                        'clk': 3012
                    },
                    'creative': {
                        'body': "blah bla",
                        '_id': "asdo2nOASINdlnasd",
                        'url': "http://www.profilebrand.com/graphics/category/animals/4904_pitbulls-are-great-dogs.png",
                        'dsp': "DSP2",
                        'crtv_id': "CREATIVE1"
                    }
                },
                'CREATIVE2': {
                    'stats': {
                        'chrg': 2340,
                        'imp': 23490,
                        'bid': 24902,
                        'bid_cnt': 2394,
                        'pub_rev': 2030,
                        'clk': 3012
                    },
                    'creative': {
                        'body': "blah bla",
                        '_id': "asdo2nOASINdlnasd",
                        'url': "http://www.profilebrand.com/graphics/category/animals/4904_pitbulls-are-great-dogs.png",
                        'dsp': "DSP2",
                        'crtv_id': "CREATIVE2"
                    }
                }
            }
        }

        creatives = [creative for creative in creative_stats[dsp_key].values()]

        return creatives




    def get_top_creatives(self, dsp_key=None, limit=None):
        if limit == None:
            limit = 3

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