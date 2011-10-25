from urllib import urlencode
from urllib2 import urlopen

import datetime

from common_templates.templatetags.filters import currency, percentage, percentage_rounded

import logging

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json


# +1 to ensure no division by 0
ctr = lambda clicks, impressions: (clicks/float(impressions+1))
ecpm = lambda revenue, impressions: (revenue/float(impressions+1))*1000

class MarketplaceStatsFetcher(object):
    _base_url = "http://mpx.mopub.com/stats"
    _inventory = "/inventory?"
    _dsp = "/dsps?"
    _creative = "/creatives?"

    def __init__(self, pub_id):
        self.pub_id = pub_id

    def _get_inventory_query(self, type, values):
        value_tuples = [(type, value) for value in values]
        return urlencode(value_tuples)

    def _get_inventory(self, start, end, apps=None, adunits=None, pubs=None):
        app_query = self._get_inventory_query('app_id', apps or [])
        adunit_query = self._get_inventory_query('adunit_id', adunits or [])
        pub_query = self._get_inventory_query('pub_id', pubs or [])

        if isinstance(start, datetime.date):
            start = start.strftime("%m-%d-%Y")

        if isinstance(end, datetime.date):
            end = end.strftime("%m-%d-%Y")

        #TODO: cleanup possible trailing &&
        url = "%s%s%s&%s&%s&%s&%s" % (self._base_url,
                                      self._inventory,
                                      app_query,
                                      adunit_query,
                                      pub_query,
                                      start,
                                      end)
        response_dict = _fetch_and_decode(url)

        stats_dict = {}
        for id, stats in response_dict.iteritems():
            counts = {"revenue": currency(stats['pub_rev']),
                      "impressions": stats['imp'],
                      "clicks": stats['clk'],
                      "ecpm": currency(ecpm(stats['pub_rev'], stats['imp'])),
                      "ctr": percentage(ctr(stats['clk'], stats['imp']))}
            stats_dict[id] = counts
        return stats_dict

    def get_app_stats(self, app_key, start, end):
        stats = self._get_inventory(apps=[app_key],
                                    start=start.strftime("%m-%d-%Y"),
                                    end=end.strftime("%m-%d-%Y"))
        return stats.get(app_key, {})


    def get_adunit_stats(self, adunit_key, start, end):
        stats = self._get_inventory(adunits=[adunit_key],
                                    start=start.strftime("%m-%d-%Y"),
                                    end=end.strftime("%m-%d-%Y"))
        return stats.get(adunit_key, {})

    def get_account_stats(self, start, end):
        stats = self._get_inventory(pubs=[self.pub_id],
                                    start=start.strftime("%m-%d-%Y"),
                                    end=end.strftime("%m-%d-%Y"))
        return stats.get(self.pub_id, {})

    def get_all_dsp_stats(self, start, end):
        url = "%s%spub_id=%s&start=%s&end=%s" % (self._base_url,
                                                 self._dsp,
                                                 self.pub_id,
                                                 start.strftime("%m-%d-%Y"),
                                                 end.strftime("%m-%d-%Y"))
        dsp = _fetch_and_decode(url)

        # Make the stats iterable so we can use them more easily in a template
        dsp_list = []
        for dsp_key, dsp in dsp.iteritems():

            dsp['key'] = dsp_key
            # these values has been kind of a pain in the ass to generate
            # in the template/on the client side, so generate them here.
            # ideally they'd be generated client side.
            dsp['stats']['ctr'] = ctr(dsp['stats']['clk'], dsp['stats']['imp'])
            dsp['stats']['ecpm'] = ecpm(dsp['stats']['pub_rev'], dsp['stats']['imp'])

            dsp_list.append(dsp)

        return dsp_list

    def get_dsp_stats(self, dsp_key, start, end):
        stats_list = self.get_all_dsp_stats(start.strftime("%m-%d-%Y"), end.strftime("%m-%d-%Y"))

        # iterate over all dsp stats to find the apropriate one.
        # since number of dsps will always be relatively small,
        # this should not be a bottleneck. Using this approach
        # so i can reuse get_all_dsp_stats.
        for stats in stats_list:
            if stats['key'] == dsp_key:
                dsp_stats = stats
                # keys are often used for front-end handlers,
                # so return the key too
                dsp_stats['key'] = dsp_key

                return dsp_stats
        return {}

    def get_creatives_for_dsp(self, dsp_key, start, end):
        url = "%s%spub_id=%s&dsp_id=%s&start=%s&end=%s" % (self._base_url,
                                                           self._creative,
                                                           self.pub_id,
                                                           dsp_key,
                                                           start.strftime("%m-%d-%Y"),
                                                           end.strftime("%m-%d-%Y"))
        creative_stats = _fetch_and_decode(url)

        creatives = [creative for creative in creative_stats[dsp_key].values()]
        for creative in creatives:
            creative['stats'].update(ctr = ctr(creative['stats']['clk'], creative['stats']['imp']))
            creative['stats'].update(ecpm = ecpm(creative['stats']['pub_rev'], creative['stats']['imp']))

        return creatives


    def get_top_creatives(self, dsp_key=None, limit=None):
        if limit == None:
            limit = 3

        return {}

def _fetch_and_decode(url):
    try:
        response = urlopen(url).read()
        logging.warn(response)
        response_dict = json.loads(response)
    except Exception, ex:
        raise MPStatsAPIException(ex)

    return response_dict


class MPStatsAPIException(Exception):
    pass


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