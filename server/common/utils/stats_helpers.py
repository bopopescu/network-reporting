from urllib import urlencode
from urllib2 import urlopen
from common.utils import date_magic
from datetime import datetime, date, time

from api.networks_helpers import get_all_stats as get_network_stats

from account.query_managers import AccountQueryManager
from advertiser.models import NetworkStates
from advertiser.query_managers import AdGroupQueryManager, \
        CampaignQueryManager

from ad_network_reports.query_managers import AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkAggregateManager
from common.constants import REPORTING_NETWORKS

from publisher.query_managers import AppQueryManager,\
     AdUnitQueryManager

from common.constants import MPX_DSP_IDS
import logging

from reporting.query_managers import StatsModelQueryManager

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json


class AbstractStatsFetcher(object):

    def __init__(self, account_key):
        self.account_key = str(account_key)

    def get_app_stats(self, app_key, start, end, daily=False):
        raise NotImplementedError('Implement this method fool')

    def get_adunit_stats(self, adunit_key, start, end, daily=False):
        raise NotImplementedError('Implement this method fool')

    def get_account_stats(self, start, end, daily=False):
        raise NotImplementedError('Implement this method fool')

    def format_stats(self, stats):
        stat_totals = {
            'rev': sum([stat.revenue for stat in stats]),
            'imp': sum([stat.impression_count for stat in stats]),
            'clk': sum([stat.click_count for stat in stats]),
            'req': sum([stat.request_count for stat in stats]),
            'conv': sum([stat.conversion_count for stat in stats]),
            'conv_rate': sum([stat.conv_rate for stat in stats])/len(stats),
        }

        return stat_totals

    def format_daily_stats(self, all_stats):
        stats_dict = {'sum': {'rev': sum([stats.revenue for stats in
                                  all_stats]),
                              'imp': sum([stats.impression_count for
                                  stats in all_stats]),
                              'clk': sum([stats.click_count for stats in
                                  all_stats]),
                              'req': sum([stats.request_count for stats
                                  in all_stats]), },
                      'daily_stats': [{'rev': stats.revenue,
                                       'imp': stats.impression_count,
                                       'clk': stats.click_count,
                                       'req': stats.request_count,} for
                                       stats in all_stats], }
        return stats_dict


class SummedStatsFetcher(AbstractStatsFetcher):

    def _get_publisher_stats(self, start, end, publisher=None,
                             advertiser=None, daily=True,
                             *args, **kwargs):
        # mongo
        days = date_magic.gen_days(start, end)
        query_manager = StatsModelQueryManager(AccountQueryManager.get(
            self.account_key))
        stats = query_manager.get_stats_for_days(publisher=publisher,
                                                 advertiser=advertiser,
                                                 days=days)
        if daily:
            return self.format_daily_stats(stats)
        else:
            return self.format_stats(stats)

    def _get_campaign_stats(self, start, end, campaign, publisher=None,
            daily=True, *args, **kwargs):
        # mongo
        query_manager = StatsModelQueryManager(AccountQueryManager.get(
            self.account_key))
        # If its a new network campaign that has been migrated and the
        # transition date is after the start date
        if campaign.is_network and \
           campaign.network_state == NetworkStates.DEFAULT_NETWORK_CAMPAIGN and \
           campaign.old_campaign and start <= campaign.transition_date:
            
            new_stats = None
            if end >= campaign.transition_date:
                # get new campaign stats
                days = date_magic.gen_days(campaign.transition_date, end)
                new_stats = query_manager.get_stats_for_days(
                        publisher=publisher, advertiser=campaign,
                        days=days)
                days = date_magic.gen_days(start, campaign.transition_date)
            else:
                # getting only legacy campaign stats
                days = date_magic.gen_days(start, end)
            # get old campaign stats
            old_stats = query_manager.get_stats_for_days(publisher=publisher,
                    advertiser=campaign.old_campaign, days=days)
            if new_stats:
                transition_stats = old_stats[-1] + new_stats[0]
                all_stats = old_stats[:-1] + [transition_stats] + new_stats[1:]
            else:
                all_stats = old_stats
        else:
            days = date_magic.gen_days(start, end)
            all_stats = query_manager.get_stats_for_days(publisher=publisher,
                    advertiser=campaign, days=days)
        if daily:
            return self.format_daily_stats(all_stats)
        else:
            return self.format_stats(all_stats)

    def get_campaign_stats(self, campaign_key, start, end, *args, **kwargs):
        # mongo
        campaign = CampaignQueryManager.get(campaign_key)
        campaign_stats = self._get_campaign_stats(start, end, campaign,
                daily=True)
        logging.warn('\n\n\n\n\n\n\n\nyeyeye')
        return campaign_stats

    def _get_advertiser_stats(self, advertiser, start, end,
                              publisher=None, *args, **kwargs):
        days = date_magic.gen_days(start, end)
        query_manager = StatsModelQueryManager(advertiser.account)
        stats = query_manager.get_stats_for_days(publisher=publisher,
                                                 advertiser=advertiser,
                                                 days=days)
        return self.format_stats(stats)

    def get_app_stats(self, app_key, start, end, *args, **kwargs):
        # mongo
        app = AppQueryManager.get(app_key)
        app_stats = self._get_publisher_stats(start, end, publisher=app)
        return app_stats

    def get_adunit_stats(self, adunit_key, start, end, daily=True):
        # mongo
        adunit = AdUnitQueryManager.get(adunit_key)
        adunit_stats = self._get_publisher_stats(start, end, publisher=adunit)
        return adunit_stats

    def get_adgroup_stats(self, adgroup, start, end, daily=True):
        if isinstance(adgroup, str):
            adgroup = AdGroupQueryManager.get(adgroup)
        adgroup_stats = self._get_advertiser_stats(adgroup, start, end)
        return adgroup_stats


    
    def get_network_app_stats(self, app_key, campaign,
                                        start, end, *args, **kwargs):
        """ This method needs to be merged """
        # mongo
        app = AppQueryManager.get(app_key)
        app_stats = self._get_campaign_stats(start, end, campaign,
                publisher=app)
        return app_stats

    def get_campaign_specific_app_stats(self, app_key, campaign_key,
                                        start, end, *args, **kwargs):
        # mongo
        app = AppQueryManager.get(app_key)
        campaign = CampaignQueryManager.get(campaign_key)
        app_stats = self._get_publisher_stats(start, end,
                                              publisher=app,
                                              advertiser=campaign)
        return app_stats

        
    def get_campaign_specific_adunit_stats(self, adunit_key,
                                           campaign_key,
                                           start, end,
                                           *args, **kwargs):
        # mongo
        adunit = AdUnitQueryManager.get(adunit_key)
        campaign = CampaignQueryManager.get(campaign_key)
        adunit_stats = self._get_publisher_stats(start, end,
                                                 publisher=adunit,
                                                 advertiser=campaign)
        return adunit_stats
        
    def get_network_adunit_stats(self, adunit_key, campaign, start,
            end, *args, **kwargs):
        # mongo
        adunit = AdUnitQueryManager.get(adunit_key);
        adunit_stats = self._get_campaign_stats(start, end, campaign,
                publisher=adunit)
        return adunit_stats

        
    def get_adgroup_specific_app_stats(self, app_key, adgroup_key,
                                        start, end, *args, **kwargs):
        # mongo
        app = AppQueryManager.get(app_key)
        adgroup = AdGroupQueryManager.get(adgroup_key)
        app_stats = self._get_publisher_stats(start, end, publisher=app,
                                              advertiser=adgroup)
        return app_stats

        
    def get_adgroup_specific_adunit_stats(self, adunit_key, adgroup_key,
                                           start, end, *args, **kwargs):
        # mongo
        adunit = AdUnitQueryManager.get(adunit_key)
        adgroup = AdGroupQueryManager.get(adgroup_key)
        adunit_stats = self._get_publisher_stats(start, end, publisher=adunit,
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

        if isinstance(start, date):
            start = start.strftime("%m-%d-%Y")

        if isinstance(end, date):
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
            counts = {"rev": float(stats['pub_rev']),
                      "imp": int(stats['imp']),
                      "clk": stats['clk'], }
            stats_dict[id] = counts
        return stats_dict

    def _get_pub_inventory(self, pub, start, end, daily=True):
        """
        This is an alternative to _get_inventory. Here, pub is used in the broad
        sense to represent a pub/app/adunit. When stats for only a single
        pub/app/adunit are necessary. The endpoint this uses is much faster
        but less flexible so this should be used whenever possible

        :param daily: when set to True, return daily breakdown of stats

        example output with daily flag set:

        {'rev': '$0.08',
        'daily': [{'rev': '$0.00',
                   'date': u'2011-10-25',
                   'imp': 0,
                   'clk': 0},
                  {'rev': '$0.01',
                   'date': u'2011-10-26',
                   'imp': 9,
                   'clk': 0},
                  {'rev': '$0.07',
                   'date': u'2011-10-27',
                   'imp': 71,
                   'clk': 0}],
         'imp': 80,
         'clk': 0}

        """
        if isinstance(start, date):
            start = start.strftime("%m-%d-%Y")

        if isinstance(end, date):
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
            counts['daily_stats'] = daily_stats_list_transformed

        stats_dict = {pub: counts}
        return stats_dict

    def get_app_stats(self, app_key, start, end, daily=True):
        stats = self._get_pub_inventory(app_key,
                                        start=start.strftime("%m-%d-%Y"),
                                        end=end.strftime("%m-%d-%Y"),
                                        daily=daily)
        return stats.get(app_key, {})


    def get_adunit_stats(self, adunit_key, start, end, daily=True):
        stats = self._get_pub_inventory(adunit_key,
                                        start=start.strftime("%m-%d-%Y"),
                                        end=end.strftime("%m-%d-%Y"),
                                        daily=daily)
        return stats.get(adunit_key, {})

    def get_account_stats(self, start, end, daily=True):
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

                all_creatives.extend(creatives)
        return all_creatives



    def get_top_creatives(self, dsp_key=None, limit=None):
        if limit == None:
            limit = 3

        return {}

class NetworkStatsFetcher(AbstractStatsFetcher):
    def _get_publisher_stats(self, start, end, account_key, app_key='*',
            network='*'):
        # network stats api
        stats = get_network_stats(str(app_key), network, str(account_key),
                start, end).values()[0]
        return stats

    def get_campaign_stats(self, campaign_key, start, end, *args, **kwargs):
        campaign = CampaignQueryManager.get(campaign_key)
        days = date_magic.gen_days(start, end)
        if campaign.network_state == \
                NetworkStates.DEFAULT_NETWORK_CAMPAIGN:
            stats = self._get_publisher_stats(start, end, campaign._account,
                    network=campaign.network_type)
        else:
            return None
        return stats

    def get_campaign_specific_app_stats(self, app_key, campaign, start, end,
            *args, **kwargs):
        app_stats = self._get_publisher_stats(start, end, campaign._account,
                app_key=app_key, network=campaign.network_type)['sum']
        return app_stats

# TODO: refactor stuff that uses this and remove it
class AdNetworkStatsFetcher(object):
    @classmethod
    def get_account_roll_up_stats(cls, account, days):
        stats_list = [AdNetworkAggregateManager.find_or_create(account, day,
                network=network, create=False) for day in days for network in
                REPORTING_NETWORKS.keys()]
        stats = AdNetworkStatsManager.roll_up_stats([stats for stats in
                stats_list if stats != None])
        return stats.dict_


    @classmethod
    def get_daily_stats(cls, account, days):
        all_stats = []
        for day in days:
            stats = AdNetworkAggregateManager.get_stats_for_day(account, day)
            stats.date = day
            all_stats.append(stats.dict_)
        return all_stats


    @classmethod
    def get_app_on_network_stats(cls, network, days, pub_id):
        mapper = AdNetworkMapperManager.get_mapper(pub_id, network)
        stats = AdNetworkStatsManager.get_stats_for_mapper_and_days(mapper,
                days)[0]
        stats_dict = stats.dict_
        app = mapper.application
        stats_dict['app_name'] = app.full_name
        stats_dict['network_name'] = REPORTING_NETWORKS[mapper.ad_network_name]
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
    return {
        "rev": stats_dict['rev'],
        "imp": int(stats_dict['imp']),
        "clk": stats_dict.get('clk', 0),
    } # no clk currently from /stats/pub


def _fetch_and_decode(url):
    try:
        response = urlopen(url).read()
        response_dict = json.loads(response)
    except Exception, ex:
        raise MPStatsAPIException(ex)

    return response_dict


class MPStatsAPIException(Exception):
    pass
