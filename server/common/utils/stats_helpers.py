from urllib import urlencode
from urllib2 import urlopen
from common.utils import date_magic
import datetime

from advertiser.query_managers import AdGroupQueryManager
from ad_network_reports.query_managers import AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkAggregateManager, \
        AD_NETWORK_NAMES

from publisher.query_managers import AppQueryManager,\
     AdUnitQueryManager, \
     AdUnitContextQueryManager
from common_templates.templatetags.filters import currency, percentage, percentage_rounded
from common.constants import MPX_DSP_IDS
import logging

from reporting.query_managers import StatsModelQueryManager
from reporting.models import StatsModel, GEO_COUNTS

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

ctr = lambda clicks, impressions: (clicks/float(impressions) if impressions
        else 0)
ecpm = lambda revenue, impressions: (revenue/float(impressions)*1000 if
        impressions else 0)
fill_rate = lambda requests, impressions: (impressions/float(requests) if
        requests else 0)


class AbstractStatsFetcher(object):

    def __init__(self, pub_id):
        self.pub_id = str(pub_id)

    def get_app_stats(self, app_key, start, end, daily=False):
        raise NotImplementedError('Implement this method fool')

    def get_adunit_stats(self, adunit_key, start, end, daily=False):
        raise NotImplementedError('Implement this method fool')

    def get_account_stats(self, start, end, daily=False):
        raise NotImplementedError('Implement this method fool')

    def format_stats(self, stats):
        stat_totals = {
            'revenue': sum([stat.revenue for stat in stats]),
            'ctr': 0.0,
            'ecpm': 0.0,
            'impressions': sum([stat.impression_count for stat in stats]),
            'clicks': sum([stat.click_count for stat in stats]),
            'requests': sum([stat.request_count for stat in stats]),
            'fill_rate': 0.0,
            'conversions': sum([stat.conversion_count for stat in stats]),
            'conversion_rate': sum([stat.conv_rate for stat in stats])/len(stats),
        }

        stat_totals['ctr'] = ctr(stat_totals['clicks'], stat_totals['impressions'])
        stat_totals['ecpm'] = ecpm(stat_totals['revenue'], stat_totals['impressions'])
        stat_totals['fill_rate'] = fill_rate(stat_totals['requests'], stat_totals['impressions'])

        return stat_totals


class SummedStatsFetcher(AbstractStatsFetcher):
    def _get_publisher_stats(self, publisher, start, end,
                             advertiser=None, *args, **kwargs):
        # mongo
        days = date_magic.gen_days(start, end)
        query_manager = StatsModelQueryManager(publisher.account)
        stats = query_manager.get_stats_for_days(publisher=publisher,
                                                 advertiser=advertiser,
                                                 days=days)
        return self.format_stats(stats)

    def get_app_stats(self, app_key, start, end, *args, **kwargs):
        # mongo
        app = AppQueryManager.get(app_key)
        app_stats = self._get_publisher_stats(app, start, end)
        return app_stats

    def get_adunit_stats(self, adunit_key, start, end, daily=False):
        # mongo
        adunit = AdUnitQueryManager.get(adunit_key)
        adunit_stats = self._get_publisher_stats(adunit, start, end)
        return adunit_stats

    def get_adgroup_specific_app_stats(self, app_key, adgroup_key,
                                        start, end, *args, **kwargs):
        # mongo
        app = AppQueryManager.get(app_key)
        adgroup = AdGroupQueryManager.get(adgroup_key)
        app_stats = self._get_publisher_stats(app, start, end,
                                              advertiser=adgroup)
        return app_stats


    def get_adgroup_specific_adunit_stats(self, adunit_key, adgroup_key,
                                           start, end, *args, **kwargs):
        # mongo
        adunit = AdUnitQueryManager.get(adunit_key)
        adgroup = AdGroupQueryManager.get(adgroup_key)
        adunit_stats = self._get_publisher_stats(adunit, start, end,
                                                 advertiser=adgroup)
        return adunit_stats



class DirectSoldStatsFetcher(AbstractStatsFetcher):
    pass


class MarketplaceStatsFetcher(object):
    _base_url = "http://mpx.mopub.com/2stats" # TODO: change back to stats not 2stats
    _inventory = "/inventory?"
    _dsp = "/dsps?"
    _creative = "/creatives?"

    _pub_inventory = "/pub?" #using this in place of _inventory for performance

    def __init__(self, pub_id):
        self.pub_id = str(pub_id)

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
        url = "%s%s%s&%s&%s&start=%s&end=%s" % (self._base_url,
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
                      "impressions": int(stats['imp']),
                      "clicks": stats['clk'],
                      "ecpm": currency(ecpm(stats['pub_rev'], stats['imp'])),
                      "ctr": percentage(ctr(stats['clk'], stats['imp']))}
            stats_dict[id] = counts
        return stats_dict

    def _get_pub_inventory(self, pub, start, end, daily=False):
        """
        This is an alternative to _get_inventory. Here, pub is used in the broad
        sense to represent a pub/app/adunit. When stats for only a single
        pub/app/adunit are necessary. The endpoint this uses is much faster
        but less flexible so this should be used whenever possible

        :param daily: when set to True, return daily breakdown of stats

        example output with daily flag set:

        {'ctr': '0.00%',
        'revenue': '$0.08',
        'daily': [{'ctr': '0.00%',
                   'revenue': '$0.00',
                   'ecpm': '$0.00',
                   'date': u'2011-10-25',
                   'impressions': 0,
                   'clicks': 0},
                  {'ctr': '0.00%',
                   'revenue': '$0.01',
                   'ecpm': '$0.89',
                   'date': u'2011-10-26',
                   'impressions': 9,
                   'clicks': 0},
                  {'ctr': '0.00%',
                   'revenue': '$0.07',
                   'ecpm': '$0.98',
                   'date': u'2011-10-27',
                   'impressions': 71,
                   'clicks': 0}],
         'ecpm': '$0.98',
         'impressions': 80,
         'clicks': 0}

        """
        if isinstance(start, datetime.date):
            start = start.strftime("%m-%d-%Y")

        if isinstance(end, datetime.date):
            end = end.strftime("%m-%d-%Y")

        url = "%s%spub=%s&start=%s&end=%s" % \
            (self._base_url,
             self._pub_inventory,
             pub,
             start,
             end)
        response_dict = _fetch_and_decode(url)
        stats_sum = response_dict['sum']
        counts = _transform_stats(stats_sum)

        if daily:
            # append daily breakdown of stats
            daily_stats_list = response_dict['daily']
            daily_stats_list_transformed = []
            for daily_stats in daily_stats_list:
                daily_stats_transformed = _transform_stats(daily_stats)
                daily_stats_transformed['date'] = daily_stats['date']
                daily_stats_list_transformed.append(daily_stats_transformed)
            counts['daily'] = daily_stats_list_transformed

        stats_dict = {pub: counts}
        return stats_dict

    def get_app_stats(self, app_key, start, end, daily=False):
        stats = self._get_pub_inventory(app_key,
                                        start=start.strftime("%m-%d-%Y"),
                                        end=end.strftime("%m-%d-%Y"),
                                        daily=daily)
        return stats.get(app_key, {})


    def get_adunit_stats(self, adunit_key, start, end, daily=False):
        stats = self._get_pub_inventory(adunit_key,
                                        start=start.strftime("%m-%d-%Y"),
                                        end=end.strftime("%m-%d-%Y"),
                                        daily=daily)
        return stats.get(adunit_key, {})

    def get_account_stats(self, start, end, daily=False):
        stats = self._get_pub_inventory(self.pub_id,
                                        start=start.strftime("%m-%d-%Y"),
                                        end=end.strftime("%m-%d-%Y"),
                                        daily=daily)
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
        if not dsp_key in creative_stats:
            return {}
        creatives = [creative for creative in creative_stats[dsp_key].values()]
        for creative in creatives:
            creative['stats'].update(ctr = ctr(creative['stats']['clk'], creative['stats']['imp']))
            creative['stats'].update(ecpm = ecpm(creative['stats']['pub_rev'], creative['stats']['imp']))

        return creatives

    def get_all_creatives(self, start, end):
        all_creatives = []
        for dsp_key in MPX_DSP_IDS:
            url = "%s%spub_id=%s&dsp_id=%s&start=%s&end=%s" % (self._base_url,
                                                               self._creative,
                                                               self.pub_id,
                                                               dsp_key,
                                                               start.strftime("%m-%d-%Y"),
                                                               end.strftime("%m-%d-%Y"))
            creative_stats = _fetch_and_decode(url)
            if dsp_key in creative_stats:
                creatives = [creative for creative in creative_stats[dsp_key].values()]
                for creative in creatives:
                    creative['stats'].update(ctr = ctr(creative['stats']['clk'], creative['stats']['imp']))
                    creative['stats'].update(ecpm = ecpm(creative['stats']['pub_rev'], creative['stats']['imp']))

                all_creatives.extend(creatives)
        return all_creatives



    def get_top_creatives(self, dsp_key=None, limit=None):
        if limit == None:
            limit = 3

        return {}


class AdNetworkStatsFetcher(object):
    @classmethod
    def get_account_roll_up_stats(cls, account, days):
        stats_list = [AdNetworkAggregateManager.find_or_create(account, day,
                network=network, create=False) for day in days for network in
                AD_NETWORK_NAMES.keys()]
        stats = AdNetworkStatsManager.roll_up_stats([stats for stats in
                stats_list if stats != None])
        return stats.dict_


    @classmethod
    def get_daily_stats(cls, account, days):
        return [AdNetworkAggregateManager.get_stats_for_day(account, day)
                .dict_ for day in days]


    @classmethod
    def get_app_on_network_stats(cls, network, days, pub_id):
        mapper = AdNetworkMapperManager.get_mapper(publisher_id=pub_id,
                ad_network_name=network)
        stats = AdNetworkStatsManager.get_stats_for_mapper_and_days(mapper,
                days)[0]
        stats_dict = stats.dict_
        app = mapper.application
        stats_dict['app_name'] = app.full_name
        stats_dict['network_name'] = AD_NETWORK_NAMES[mapper.ad_network_name]
        stats_dict['mapper_key'] = str(mapper.key())
        stats_dict['app_key'] = app.key_
        return stats_dict


    @classmethod
    def get_roll_up_stats(cls, account, days, network=None, app=None):
        stats_list = [stats for stats in [AdNetworkAggregateManager.
                find_or_create(account, day, network=network, app=app,
                    create=False) for day in days] if stats != None]
        stats = AdNetworkStatsManager.roll_up_stats(stats_list)
        stats_dict = stats.dict_

        if network and stats_list:
            # Get the last sync date
            sync_date = stats_list[-1].date
            stats_dict['sync_date'] = sync_date.strftime('%b %d, %Y');

        return stats_dict


# Helper/Utility functions

def _transform_stats(stats_dict):
    return {"revenue": stats_dict['rev'],
            "impressions": int(stats_dict['imp']),
            "clicks": stats_dict.get('clk', 0), # no clk currently from /stats/pub
            "ecpm": ecpm(stats_dict['rev'], stats_dict['imp']),
            "ctr": ctr(stats_dict.get('clk', 0), stats_dict['imp'])}


def _fetch_and_decode(url):
    try:
        logging.warn(url)
        response = urlopen(url).read()
        response_dict = json.loads(response)
    except Exception, ex:
        raise MPStatsAPIException(ex)

    return response_dict


class MPStatsAPIException(Exception):
    pass
