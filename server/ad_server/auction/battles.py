import logging

from ad_server.filters.filters import (budget_filter,
                                    active_filter,
                                    kw_filter,
                                    geo_filter,
                                    mega_filter,
                                    format_filter,
                                    exclude_filter,
                                    freq_filter,
                                    alloc_filter,
                                    lat_lon_filter,
                                    os_filter,
                                   )


from ad_server.optimizer import optimizer
from ad_server.debug_console import trace_logging

from stats import stats_accumulator

from ad_server.networks.server_side import ServerSideException
import urllib
from common.utils import simplejson
from google.appengine.api import urlfetch, memcache

from ad_server import frequency_capping
from userstore.query_managers import ImpressionEventManager
from userstore.models import HourlyImpressionEvent, DailyImpressionEvent
# TODO: Use these helpers 'to_uni', 'to_ascii'
from common.utils.helpers import to_uni, to_ascii

import random

from ad_server.networks.get_serverside import get_serverside_for_creative

class Battle(object):
    """ Determines the best creative available within a subset of adgroups.
        Essentially a sub-auction on some subset of adgroups. """

    starting_message = "Beginning priority level x ..."

    campaign_type = "gtee_x" # These define the adgroup levels

    def __init__(self, client_context, adunit_context):
        self.client_context = client_context
        self.adunit_context = adunit_context

    def _sort_creatives(self, creatives):
        """ Sorts a list of creatives in place. Sorts by the ecpm of each
            creative-adunit pairing in descending value """

        # Build a dict {creative: ecpm}
        creative_ecpm_dict = optimizer.get_ecpms(self.adunit_context,
                                                 creatives,
                                                 sampling_fraction=0.0)

        for creative in creatives:
            creative._battle_ecpm = creative_ecpm_dict[creative]

        # We make a comparator function for sorting by ecpm
        def calc_ecpm_with_noise(creative):
            # Build in tiny, insignificant amount of random noise to break ties
            noise = random.random() * 10 ** -9

            # Make this negative so high ecpm comes first, add noise
            return -creative._battle_ecpm + noise

        # Sort using the ecpm as the key.
        return sorted(creatives, key=calc_ecpm_with_noise)


    def _get_adgroups_for_level(self):
        """ Retrieves the appropriate adgroups from the adunit_context """
        all_adgroups = self.adunit_context.adgroups
        return [adgroup for adgroup in all_adgroups
                    if adgroup.campaign.campaign_type == self.campaign_type]

    def _filter_adgroups(self, adgroups):
        """ Runs the set of adgroup filters on our adgroups.
            Returns a filtered subset of adgroups. """

        # TODO: refactor logging on filters (make them oo)

        # Build a list of all the users' frequency capping info we care about.
        # user_frequency_capping_keys = []
        #         for adgroup in adgroups:
        #             daily_key = frequency_capping.\
        #                 memcache_key_for_date(self.client_context.raw_udid,
        #                                       self.client_context.now,
        #                                       adgroup.key())
        #             user_frequency_capping_keys.append(daily_key)
        # 
        #             hourly_key = frequency_capping.\
        #                 memcache_key_for_hour(self.client_context.raw_udid,
        #                                       self.client_context.now,
        #                                       adgroup.key())
        #             user_frequency_capping_keys.append(hourly_key)
        # 
        #         # Get all users with a batch get for speed.
        #         if user_frequency_capping_keys:
        #             # user_frequency_capping_key --> # impressions for that timerange
        #             frequency_cap_dict = memcache.\
        #                                     get_multi(user_frequency_capping_keys)
        #         else:
        #             frequency_cap_dict = {}
        
        udid = self.client_context.raw_udid
        imps = ImpressionEventManager().get_impression_events(udid, 
                                                             [str(ag.key()) for ag in adgroups], 
                                                             self.client_context.now)
        frequency_cap_dict = {}                                                     
        for imp in imps:
            if imp:
                if isinstance(imp, HourlyImpressionEvent):
                    key = frequency_capping.memcache_key_for_hour(imp.udid,
                                                                  imp.time,
                                                                  imp.adgroup_id)
                if isinstance(imp, DailyImpressionEvent):
                    key = frequency_capping.memcache_key_for_date(imp.udid,
                                                                  imp.time,
                                                                  imp.adgroup_id)
            
                frequency_cap_dict[key] = imp.count
                

        adgroup_filters = (exclude_filter(self.client_context.\
                                            excluded_adgroup_keys),
                           active_filter(),
                           lat_lon_filter(self.client_context.ll),
                           kw_filter(self.client_context.keywords),
                           geo_filter(self.client_context.geo_predicates),
                           os_filter(self.client_context.user_agent),
                           freq_filter('daily', frequency_capping.\
                                                    memcache_key_for_date,
                                       self.client_context.raw_udid,
                                       self.client_context.now,
                                       frequency_cap_dict),
                           freq_filter('hourly', frequency_capping.\
                                                    memcache_key_for_hour,
                                       self.client_context.raw_udid,
                                       self.client_context.now,
                                       frequency_cap_dict),
                           budget_filter(),
                           alloc_filter())
                           # Run budget last b/c it touches memcache


        filtered_adgroups = filter(mega_filter(*adgroup_filters), adgroups)
        for (func, warn, removed_adgroup_list) in adgroup_filters:
            func = func # quiet PyLint
            if removed_adgroup_list:
                trace_logging.info(warn % ", ".join([a.name.encode('utf8') \
                                        for a in removed_adgroup_list]))
        return filtered_adgroups


    def _filter_creatives(self, creatives):
        """ Runs the set of creative filters on our creatives.
            Returns a filtered subset of creatives. """

        # TODO: refactor logging on filters (make them oo)

        creative_filters = [format_filter(self.client_context.adunit)]

        filtered_creatives = filter(mega_filter(*creative_filters), creatives)

        for (func, warn, removed_creative_list) in creative_filters:
            func = func # quiet PyLint
            if removed_creative_list:
                trace_logging.info(warn % ", ".join([c.name.encode('utf8') \
                                        for c in removed_creative_list]))


        return filtered_creatives


    def _process_winner(self, creative):
        """ Processes the winning creative. Requests it using an rpc
            if necessary. Throws an exception if an error occurs. """

        # regardless of outcome, exclude
        self.client_context.excluded_adgroup_keys.append(
                                str(creative.adgroup.key()))

        return creative

    def run(self):
        """ Runs the sub-auction"""
        adgroups = self._get_adgroups_for_level()

        trace_logging.info("=================================")
        trace_logging.info(self.__class__.starting_message)

        if not adgroups:
            trace_logging.info(u"No adgroups for this level.")
            return

        trace_logging.info(u"Available adgroups are: %s" %
                            ", ".join(["%s" % a.name for a in adgroups]))
        trace_logging.info(u"Running adgroup filters...")
        filtered_adgroups = self._filter_adgroups(adgroups)

        if not filtered_adgroups:
            trace_logging.info(u"No adgroups for this level passed filters.")
            return

        trace_logging.info(u"Filtered adgroups are: %s" %
                    ", ".join(["%s" % a.name for a in filtered_adgroups]))

        creatives = self.adunit_context.\
                        get_creatives_for_adgroups(filtered_adgroups)
        trace_logging.info("---------------------------------")
        trace_logging.info(u"Creatives from filtered adgroups are: %s" %
                    ", ".join(["%s" % a.name for a in creatives]))
        trace_logging.info(u"Running creative filters...")
        filtered_creatives = self._filter_creatives(creatives)
        if not filtered_creatives:
            trace_logging.info(u"No creatives for this level passed filters.")
            return



        # Sorted creatives are in order of descending value
        sorted_creatives = self._sort_creatives(filtered_creatives)
        trace_logging.info("---------------------------------")
        trace_logging.info(u"Filtered creatives are: %s" %
                    ", ".join(["%s" % a.name for a in sorted_creatives]))
        for creative in sorted_creatives:

            processed_creative = self._process_winner(creative)

            # Break if we successfully processed
            if processed_creative:
                return processed_creative


class GteeHighBattle(Battle):
    """ Runs the standard battle for all guaranteed campaigns. """

    starting_message = "Beginning guaranteed high campaigns..."
    campaign_type = "gtee_high"


class GteeBattle(Battle):
    """ Runs the standard battle for all guaranteed campaigns. """

    starting_message = "Beginning guaranteed campaigns..."
    campaign_type = "gtee"



class GteeLowBattle(Battle):
    """ Runs the standard battle for all guaranteed campaigns. """

    starting_message = "Beginning guaranteed low campaigns..."
    campaign_type = "gtee_low"

class PromoBattle(Battle):
    """ Runs the standard battle for all promotional campaigns. """

    starting_message = "Beginning promotional campaigns..."
    campaign_type = "promo"

class MarketplaceBattle(Battle):
    """ Queries out to the marketplace """

    starting_message = "Beginning marketplace campaigns..."
    campaign_type = "marketplace"

    def __init__(self, client_context, adunit_context, proxy_bids=None):
        """ Marketplace Battles can take in proxy_bids """
        self.proxy_bids = proxy_bids or []
        super(MarketplaceBattle, self).__init__(client_context, adunit_context)

    def _filter_creatives(self, creatives):
        """
        Returns only the first marketplace creatives
        TODO: shouldn't be possible
        """
        filtered_creatives = super(MarketplaceBattle, self).\
                                _filter_creatives(creatives)
        return filtered_creatives[:1]


    def _process_winner(self, creative):
        """ Fan out to the marketplace and see if there is a bid """
        mk_args = self.client_context.make_marketplace_dict(
                                                self.adunit_context)
        # add proxy_bids
        if self.proxy_bids:
            mk_args.update(bid_proxy=','.join([str(bid) for
                                            bid in self.proxy_bids]))

        # override pricefloor at the adgroup level
        if creative.adgroup.mktplace_price_floor:
            mk_args['price_floor'] = creative.adgroup.mktplace_price_floor

        trace_logging.info("\nSending to MPX: %s\n" % mk_args)

        mpx_url = 'http://mpx.mopub.com/req?' + self._dict_url_params(mk_args)

        trace_logging.info('URL: %s' % mpx_url)

        xhtml = None
        charge_price = None

        # set the creative as having done w/e
        # TODO: Use charge_price in logging
        stats_accumulator.log(None, event=stats_accumulator.REQ_EVENT,
                       adunit=self.adunit_context.adunit,
                       creative=creative,
                       user_agent=self.client_context.user_agent,
                       udid=self.client_context.raw_udid)
        try:
            fetched = urlfetch.fetch(mpx_url, deadline=2)
            # Make sure it's a good response
            trace_logging.warning('MPX RESPONES CODE:%s'%fetched.status_code)
            if fetched.status_code == 200:
                creative = self._process_marketplace_response(fetched.content,
                                                              creative)
                if creative:
                    # modify the height and width to be that of the adunit
                    creative.width = self.client_context.adunit.get_width()
                    creative.height = self.client_context.adunit.get_height()
                    # Do not ever add marketplace adgroups to
                    # the excluded_adgroup_keys hence don't call super
                    return creative
                return None
        except Exception, e: # TODO: catch real exception
            # There was no valid bid
            return None

    def _dict_url_params(self, params):
        """
        re-write of urllib.urlencode to take lists
        """
        query_string = ''
        for key, value in params.iteritems():
            if not isinstance(value, (list, tuple)):
                value = [value]
            new_string = '&'.join(['%s=%s' % (urllib.quote(str(key)),urllib.quote(str(elem))) for elem in value])
            # don't ad & at the end
            if query_string:
                query_string += '&' + new_string
            else:
                query_string = new_string
        return query_string

    def _process_marketplace_response(self, content, creative):
        """ NOTE: pub_rev is CPM this means that the pub is paid
            pub_rev / 1000
            Further, the bid_strategy for the adgroup is always "cpm"
        """
        marketplace_response_dict = simplejson.loads(content)
        trace_logging.info('MPX REPSONSE:%s'%marketplace_response_dict)
        # With valid data
        if marketplace_response_dict.get('xhtml_real', None) and \
                marketplace_response_dict.get('revenue', None):
            creative.html_data = marketplace_response_dict['xhtml_real']
            pub_rev = marketplace_response_dict['revenue']
            # Should really be the pub's cut
            # Do we need to do anything with the bid info?
            trace_logging.info('\n\nMPX Charge: %s\nMPX HTML: %s\n' %
                            (pub_rev, creative.html_data))

            # Attach bid to adgroup - see docstring for details on pub_rev
            # and bid
            creative.adgroup.bid = pub_rev
            return creative

class NetworkBattle(Battle):
    """ Fans out to each of the networks """

    starting_message = "Beginning network campaigns..."
    campaign_type = "network"

    def __init__(self, client_context, adunit_context, min_cpm=0.0):
        """ Network Battles can take an additional parameter"""
        self.min_cpm = min_cpm

        # cache so we don't calculate this more than once
        self._filtered_adgroups = None
        self._filtered_creatives = None
        self._sorted_creatives = None

        super(NetworkBattle, self).__init__(client_context, adunit_context)

    def _filter_adgroups(self, adgroups):
        """
        returns the filtered adgroups from the cache
        or calculates for the first time
        """
        # if in the cache return, else do the hard work
        # we use != None, b/c empty list [] means the value
        # has already been calculated
        if self._filtered_adgroups != None:
            return self._filtered_adgroups
        else:
            # get and put in the cache
            self._filtered_adgroups = super(NetworkBattle, self).\
                                        _filter_adgroups(adgroups)
            return self._filtered_adgroups

    def _filter_creatives(self, creatives):
        # if in the cache return, else do the hard work
        # we use != None, b/c empty list [] means the value
        # has already been calculated
        if self._filtered_creatives != None:
            return self._filtered_creatives
        else:
            self._filtered_creatives = super(NetworkBattle, self).\
                                        _filter_creatives(creatives)
            return self._filtered_creatives

    def _sort_creatives(self, creatives):
        # if in the cache return, else do the hard work
        # we use != None, b/c empty list [] means the value
        # has already been calculated
        if self._sorted_creatives != None:
            return self._sorted_creatives
        else:
            # get and put in the cache
            self._sorted_creatives = super(NetworkBattle, self).\
                                        _sort_creatives(creatives)
            return self._sorted_creatives

    def bids_for_level(self):
        """
        Returns all bids for this level after filtering
        and using the optimizer to calculate eCPMs
        """

        adgroups = self._get_adgroups_for_level()
        filtered_adgroups = self._filter_adgroups(adgroups)

        creatives = self.adunit_context.\
                        get_creatives_for_adgroups(filtered_adgroups)
        filtered_creatives = self._filter_creatives(creatives)
        sorted_creatives = self._sort_creatives(filtered_creatives)
        return [creative._battle_ecpm for creative in sorted_creatives]

    def _process_winner(self, creative):
        """ Fan out to a network and see if it can fill the adunit. """

        # If the ecpm for the network is less than the min_cpm, drop it
        if creative._battle_ecpm < self.min_cpm:
            return False

        # TODO: refactor logging
        stats_accumulator.log(None,
                       event=stats_accumulator.REQ_EVENT,
                       adunit=self.client_context.adunit,
                       creative=creative,
                       user_agent=self.client_context.user_agent,
                       udid=self.client_context.raw_udid,
                       country_code=self.client_context.country_code)

        creative.ServerSide = get_serverside_for_creative(creative)
        # If the network is a native network, then it does not require an rpc
        if not creative.ServerSide:
            return super(NetworkBattle, self)._process_winner(creative)

        # All non-native networks need rpcs
        else:
            server_side = creative.ServerSide(self.client_context,
                                              self.adunit_context.adunit)
            try:
                # Right now we make the call, and synchronously get the reponse
                creative.html_data = server_side.\
                                make_call_and_get_html_from_response()
                if server_side.creative_width:
                    creative.width = server_side.creative_width
                if server_side.creative_height:
                    creative.height = server_side.creative_height
                return super(NetworkBattle, self)._process_winner(creative)
            except ServerSideException:
                # call the super class so that the exclude parameter is properly set
                super(NetworkBattle, self)._process_winner(creative)
                return False
                # log


class BackfillPromoBattle(PromoBattle):
    starting_message = "Beginning backfill promotional campaigns..."
    campaign_type = "backfill_promo"
