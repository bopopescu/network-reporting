
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


ctr = lambda clicks, impressions: (clicks/float(impressions))
ecpm = lambda revenue, impressions: (revenue/float(impressions))*1000

class MarketplaceStatsFetcher(object):
    def __init__(self, account_keys):
        self.account_keys = account_keys
        self.payload = {}

    def get_app_stats(self, app_key):
        imp = random.randint(1, 100000)
        rev =  random.randint(1, 100000)
        clk = random.randint(1, imp/10)

        return {
            "revenue": currency(rev),
            "impressions": imp,
            "clicks": clk,
            "ecpm": currency(ecpm(clk, imp)),
            "ctr": percentage(ctr(rev, imp))
        }


    def get_adunit_stats(self, adunit_key):
        imp = random.randint(1, 100000)
        rev =  random.randint(1, 100000)
        clk = random.randint(1, imp/10)

        return {
            "revenue": currency(rev),
            "impressions": imp,
            "clicks": clk,
            "ecpm": currency(ecpm(clk, imp)),
            "ctr": percentage(ctr(rev, imp))
        }


    def get_account_stats(self, account_key):
        imp = random.randint(1, 100000)
        rev =  random.randint(1, 100000)
        clk = random.randint(1, imp/10)

        return {
            "revenue": currency(rev),
            "impressions": imp,
            "clicks": clk,
            "ecpm": currency(ecpm(clk, imp)),
            "ctr": percentage(ctr(rev, imp))
        }


    def get_all_dsp_stats(self, start, end):
        dsps = {
            "DSP1": {
                "url": "http://www.google.com/",
                "name": "AdBlah",
                "advertiser": "stfu.com",
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
                "advertiser": "stfu.com",
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

        # Make the stats iterable so we can use them more easily in a template
        dsp_list = []
        for dsp_key, dsp in dsps.iteritems():

            dsp['key'] = dsp_key
            # these values has been kind of a pain in the ass to generate
            # in the template/on the client side, so generate them here.
            # ideally they'd be generated client side.
            dsp['stats']['ctr'] = ctr(dsp['stats']['clk'], dsp['stats']['imp'])
            dsp['stats']['ecpm'] = ecpm(dsp['stats']['clk'], dsp['stats']['pub_rev'])

            dsp_list.append(dsp)

        return dsp_list

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
                        'advertiser': 'hobmob.com',
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
                        'advertiser': 'ad-yo.com',
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
                        'advertiser': 'hobmob.com',
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
                        'advertiser': 'ads.com',
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
        for creative in creatives:
            creative['stats'].update(ctr = ctr(creative['stats']['clk'], creative['stats']['imp']))
            creative['stats'].update(ecpm = ecpm(creative['stats']['clk'], creative['stats']['pub_rev']))

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