from ad_server.filters.filters import (budget_filter,
                                    active_filter,
                                    kw_filter,
                                    geo_filter,
                                    device_filter,
                                    mega_filter,
                                    format_filter,
                                    exclude_filter,
                                    ecpm_filter,
                                    freq_filter,
                                    all_freq_filter,
                                    lat_lon_filter,
                                    os_filter,
                                   )       
                                   
                                   
from ad_server.networks.appnexus import AppNexusServerSide
from ad_server.networks.brightroll import BrightRollServerSide
from ad_server.networks.chartboost import ChartBoostServerSide
from ad_server.networks.ejam import EjamServerSide
from ad_server.networks.greystripe import GreyStripeServerSide
from ad_server.networks.inmobi import InMobiServerSide
from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.mobfox import MobFoxServerSide 

                            
from ad_server.optimizer import optimizer                                   
from ad_server.debug_console import trace_logging     

from common.utils.marketplace_helpers import build_marketplace_dict  
from mopub_logging import mp_logging       

NATIVE_REQUESTS = ['admob', 'adsense', 'iAd', 'custom', 'custom_native', 'admob_native', 'millennial_native']      


SERVER_SIDE_DICT = {"millennial":MillennialServerSide,
                    "appnexus":AppNexusServerSide,
                    "inmobi":InMobiServerSide,
                    "brightroll":BrightRollServerSide,
                    "chartboost":ChartBoostServerSide,
                    "ejam":EjamServerSide,
                    "jumptap":JumptapServerSide,
                    "greystripe":GreyStripeServerSide,
                    "mobfox":MobFoxServerSide,}
 
class Battle(object):
    """ Determines the best creative available within a subset of adgroups.
        Essentially a sub-auction on some subset of adgroups. """  
    
    starting_message = "Beginning priority level x ..."     
    
    def __init__(self, battle_context, adunit_context):
        self.battle_context = battle_context
        self.adunit_context = adunit_context
    
    def _sort_creatives(self, creatives): 
        """ Sorts a list of creatives in place. Sorts by the ecpm of each
            creative-adunit pairing in descending value """   
        
        # Build a dict {creative: ecpm}
        creative_ecpm_dict = optimizer.get_ecpms(self.adunit_context,
                                                 creatives,
                                                 sampling_fraction=0.0)

        # Make this negative so high ecpm comes first
        ecpm_lookup = lambda creative: -creative_ecpm_dict[creative]   
        
        # Sort using the ecpm as the key.
        return sorted(creatives, key=ecpm_lookup)
        
    
    def _get_adgroups_for_level(self):
        """ Retrieves the appropriate adgroups from the adunit_context """ 
        
        # Base case, return all targeted adgroups
        
        return adunit_context.adgroups
        
    
    def _filter_adgroups(self, adgroups):
        """ Runs the set of adgroup filters on our adgroups.
            Returns a filtered subset of adgroups. """         
        
        # TODO: refactor logging on filters (make them oo) 
        
        adgroup_filters = (exclude_filter(self.battle_context.excluded_adgroup_keys),
                           active_filter(), 
                           lat_lon_filter(self.battle_context.ll),
                           kw_filter(self.battle_context.keywords), 
                           geo_filter(self.battle_context.geo_predicates),
                           os_filter(self.battle_context.user_agent),
                           budget_filter()) # Run budget last b/c it touches memcache        
         
         
                       
        filtered_adgroups = filter(mega_filter(*adgroup_filters), adgroups)
        for (func, warn, removed_adgroup_list) in adgroup_filters:
            trace_logging.info(warn % ", ".join([a.name.encode('utf8') for a in removed_adgroup_list])) 
        return filtered_adgroups   
        
        
    def _filter_creatives(self, creatives):      
        """ Runs the set of creative filters on our creatives.
            Returns a filtered subset of creatives. """ 

        # TODO: refactor logging on filters (make them oo) 
        
        creative_filters = [format_filter(self.battle_context.adunit)]
        
        filtered_creatives = filter(mega_filter(*creative_filters), creatives)
        return filtered_creatives   
         
    
    def _process_winner(self, creative):
        """ Processes the winning creative. Requests it using an rpc if necessary.
            Throws an exception if an error occurs. """
        
        # regardless of outcome, exclude
        self.battle_context.excluded_adgroup_keys.append(str(creative.adgroup.key()))
  
        return creative  
       
    def run(self):                             
        """ Runs the sub-auction"""
        adgroups = self._get_adgroups_for_level()
    
        trace_logging.info(self.__class__.starting_message)
        
        trace_logging.info("Available adgroups are: %s" % adgroups)    
         
        filtered_adgroups = self._filter_adgroups(adgroups)
        
        trace_logging.info("Filtered adgroups are: %s" % filtered_adgroups)
    
        # TODO: Add in frequency capping.
    
        creatives = self.adunit_context.get_creatives_for_adgroups(filtered_adgroups)   
    
        filtered_creatives = self._filter_creatives(creatives)
        
        # Sorted creatives are in order of descending value
        sorted_creatives = self._sort_creatives(filtered_creatives)
    
        for creative in sorted_creatives:   
            
            return self._process_winner(creative) 
            
            # try:
            #                return self._process_winner(creative) 
            #            except: 
            #                trace_logging.info("Processing of creative: %s failed" % creative)  
            #                                               
                                                    
class GteeHighBattle(Battle):  
    """ Runs the standard battle for all guaranteed campaigns. """
    
    starting_message = "Beginning guaranteed high campaigns..."         
    
    def _get_adgroups_for_level(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "gtee_high", all_adgroups)
        
class GteeBattle(Battle):  
    """ Runs the standard battle for all guaranteed campaigns. """

    starting_message = "Beginning guaranteed campaigns..."         

    def _get_adgroups_for_level(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "gtee", all_adgroups)               

class GteeLowBattle(Battle):  
    """ Runs the standard battle for all guaranteed campaigns. """

    starting_message = "Beginning guaranteed low campaigns..."         

    def _get_adgroups_for_level(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "gtee_low", all_adgroups)
                                                                                            
    

class PromoBattle(Battle):  
    """ Runs the standard battle for all promotional campaigns. """

    starting_message = "Beginning promotional campaigns..."         

    def _get_adgroups_for_level(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "promo", all_adgroups)   
        
  
class MarketplaceBattle(Battle):  
    """ Queries out to the marketplace """

    starting_message = "Beginning marketplace campaigns..."         

    def _get_adgroups_for_level(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "marketplace", all_adgroups) 
        
    def _process_winner(self, creative):    
        """ Fan out to the marketplace and see if there is a bid """    
        # TODO: Can we get relevant information without passing request
        mk_args = build_marketplace_dict(adunit=self.battle_contextadunit,
                                         kws=self.battle_context.keywords,
                                         udid=self.battle_context.udid,
                                         ua=self.battle_context.user_agent,
                                         ll=self.battle_context.ll,
                                         ip=request.remote_addr,
                                         adunit_context=self.adunit_context,
                                         # country=helpers.get_country_code(request.headers, default=None),
                                         country=self.battle_context.country_code)
class NetworkBattle(Battle):  
    """ Fans out to each of the networks """
    
    starting_message = "Beginning marketplace campaigns..."         
    
    def _get_adgroups_for_level(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "network", all_adgroups) 
    
    def _process_winner(self, creative):    
        """ Fan out to each networks and see if it can fill the request. """ 
        # If the network is a native network, then it does not require an rpc
        if creative.adgroup.network_type in NATIVE_REQUESTS: 

            # TODO: refactor logging
            mp_logging.log(None, 
                           event=mp_logging.REQ_EVENT, 
                           adunit=self.battle_context.adunit, 
                           creative=creative, 
                           user_agent=self.battle_context.user_agent,   
                           udid=self.battle_context.udid,
                           country_code=self.battle_context.country_code)
            return super(NetworkBattle, self)._process_winner(creative)
        
        # All non-native networks need rpcs    
        else:
            ServerSideClass = SERVER_SIDE_DICT[creative.adgroup.network_type]
            
               
            @classmethod
            def request_third_party_server(cls,request,adunit,adgroups):
                if not isinstance(adgroups,(list,tuple)):
                    multiple = False
                    adgroups = [adgroups]
                else:
                    multiple = True    
                rpcs = []
                for adgroup in adgroups:
                    if adgroup.network_type in SERVER_SIDE_DICT:
                        KlassServerSide = SERVER_SIDE_DICT[adgroup.network_type]
                        server_side = KlassServerSide(request, adunit) 
                        trace_logging.warning("%s url %s"%(KlassServerSide,server_side.url))

                        rpc = urlfetch.create_rpc(2) # maximum delay we are willing to accept is 2000 ms
                        payload = server_side.payload
                        trace_logging.warning("payload: %s"%payload)
                        trace_logging.warning("headers: %s"%server_side.headers)
                        if payload == None:
                            urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers)
                        else:
                            urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers, method=urlfetch.POST, payload=payload)
                        # attaching the adgroup to the rpc
                        rpc.adgroup = adgroup
                        rpc.serverside = server_side
                        rpcs.append(rpc)
                return rpcs if multiple else rpcs[0]    
        
            
        
            
    
    
    
    
        

        
        
        
        
