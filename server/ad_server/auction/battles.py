from ad_server.filters.filters import (budget_filter,
                                    active_filter,
                                    kw_filter,
                                    geo_filter,    
                                    mega_filter,
                                    format_filter,
                                    exclude_filter,
                                    ecpm_filter,
                                    freq_filter,
                                    all_freq_filter,
                                    lat_lon_filter,
                                    os_filter,
                                   )       

                            
from ad_server.optimizer import optimizer                                   
from ad_server.debug_console import trace_logging     

from common.utils.marketplace_helpers import build_marketplace_dict  
from mopub_logging import mp_logging      

from ad_server.networks.server_side import ServerSideException 

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

        # Make this negative so high ecpm comes first
        ecpm_lookup = lambda creative: -creative_ecpm_dict[creative]   
        
        # Sort using the ecpm as the key.
        return sorted(creatives, key=ecpm_lookup)
        
    
    def _get_adgroups_for_level(self):
        """ Retrieves the appropriate adgroups from the adunit_context """ 
        all_adgroups = self.adunit_context.adgroups    
        return filter(lambda ag: ag.campaign.campaign_type == self.__class__.campaign_type, all_adgroups)
            
    def _filter_adgroups(self, adgroups):
        """ Runs the set of adgroup filters on our adgroups.
            Returns a filtered subset of adgroups. """         
        
        # TODO: refactor logging on filters (make them oo) 
        
        adgroup_filters = (exclude_filter(self.client_context.excluded_adgroup_keys),
                           active_filter(), 
                           lat_lon_filter(self.client_context.ll),
                           kw_filter(self.client_context.keywords), 
                           geo_filter(self.client_context.geo_predicates),
                           os_filter(self.client_context.user_agent),
                           budget_filter()) # Run budget last b/c it touches memcache        
         
         
                       
        filtered_adgroups = filter(mega_filter(*adgroup_filters), adgroups)
        for (func, warn, removed_adgroup_list) in adgroup_filters:
            trace_logging.info(warn % ", ".join([a.name.encode('utf8') for a in removed_adgroup_list])) 
        return filtered_adgroups   
        
        
    def _filter_creatives(self, creatives):      
        """ Runs the set of creative filters on our creatives.
            Returns a filtered subset of creatives. """ 

        # TODO: refactor logging on filters (make them oo) 
        
        creative_filters = [format_filter(self.client_context.adunit)]
        
        filtered_creatives = filter(mega_filter(*creative_filters), creatives)
        return filtered_creatives   
         
    
    def _process_winner(self, creative):
        """ Processes the winning creative. Requests it using an rpc if necessary.
            Throws an exception if an error occurs. """
        
        # regardless of outcome, exclude
        self.client_context.excluded_adgroup_keys.append(str(creative.adgroup.key()))
  
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
    
    def _process_winner(self, creative):    
        """ Fan out to the marketplace and see if there is a bid """    
        # TODO: Can we get relevant information without passing request
        mk_args = build_marketplace_dict(adunit=self.client_context.adunit,
                                         kws=self.client_context.keywords,
                                         udid=self.client_context.udid,
                                         ua=self.client_context.user_agent,
                                         ll=self.client_context.ll,
                                         ip=request.remote_addr,
                                         adunit_context=self.adunit_context,
                                         # country=helpers.get_country_code(request.headers, default=None),
                                         country=self.client_context.country_code) 
                                         
class NetworkBattle(Battle):  
    """ Fans out to each of the networks """

    starting_message = "Beginning marketplace campaigns..."
    campaign_type = "network"         
   
    def _process_winner(self, creative):    
        """ Fan out to a network and see if it can fill the request. """ 
        # If the network is a native network, then it does not require an rpc   

        if not creative.ServerSide: 

            # TODO: refactor logging
            mp_logging.log(None, 
                           event=mp_logging.REQ_EVENT, 
                           adunit=self.client_context.adunit, 
                           creative=creative, 
                           user_agent=self.client_context.user_agent,   
                           udid=self.client_context.raw_udid,
                           country_code=self.client_context.country_code)     
                           
            return super(NetworkBattle, self)._process_winner(creative)
        
        # All non-native networks need rpcs    
        else:
            server_side = creative.ServerSide(self.client_context, self.adunit_context.adunit)
            try: 
                # Right now we make the call, and synchronously get the reponse
                creative.html = server_side.make_call_and_get_html_from_response()  
                return super(NetworkBattle, self)._process_winner(creative)  
            except ServerSideException:
                return False
                # log
                
                
class BackfillPromoBattle(PromoBattle):   
    starting_message = "Beginning promotional campaigns..."         
    campaign_type = "backfill_promo"
                   
                            
class BackfillMarketplaceBattle(MarketplaceBattle):         
    starting_message = "Beginning backfill marketplace campaigns..."         
    campaign_type = "backfill_marketplace"
            
            
    
    
    
    
        

        
        
        
        
