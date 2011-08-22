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
from ad_server.optimizer import optimizer                                   
from ad_server.debug_console import trace_logging      
class Battle(object):
    """ Determines the best creative available within a subset of adgroups.
        Essentially a sub-auction on some subset of adgroups. """  
    
    starting_message = "Beginning priority level x ..."     
    
    def __init__(self, battle_context, adunit_context):
        self.battle_context = battle_context
        self.adunit_context = adunit_context
    
    def _sort_creatives(self, creatives): 
        """ Sorts a list of creatives in place. Sorts by the ecpm of each
            creative-adunit pairing """   
        
        creative_ecpm_dict = optimizer.get_ecpms(self.adunit_context,
                                                 creatives,
                                                 sampling_fraction=0.0)
        
        
        # Make this negative so high ecpm comes first
        ecpm_lookup = lambda creative: -creative_ecpm_dict[creative]   
        
        # Sort using the ecpm as the key.
        return sorted(creatives, key=ecpm_lookup)
        
    
    def _get_adgroups(self):
        """ Retrieves the appropriate adgroups from the adunit_context """ 
        
        # Base case, return all targeted adgroups
        
        return adunit_context.adgroups
        
    
    def _filter_adgroups(self, adgroups):
        """ Runs the set of adgroup filters on our adgroups """         
        
        # TODO: refactor logging on filters (make them oo) 
        
        adgroup_filters = (exclude_filter(self.battle_context.excluded_adgroup_keys),
                           active_filter(), 
                           lat_lon_filter(self.battle_context.ll),
                           kw_filter(self.battle_context.keywords), 
                           geo_filter(self.battle_context.geo_predicates),
                           os_filter(self.battle_context.user_agent),
                           budget_filter())         
                       
        filtered_adgroups = filter(mega_filter(*adgroup_filters), adgroups)
        for (func, warn, removed_adgroup_list) in adgroup_filters:
            trace_logging.info(warn % ", ".join([a.name.encode('utf8') for a in removed_adgroup_list])) 
        return filtered_adgroups   
        
        
    def _filter_creatives(self, creatives):      
        """ Runs the set of creative filters on our creatives """ 

        # TODO: refactor logging on filters (make them oo) 
        
        creative_filters = [format_filter(self.battle_context.adunit)]
        
        filtered_creatives = filter(mega_filter(*creative_filters), creatives)
        return filtered_creatives   
         
    
    def _process_winner(self, creative):
        """ Processes the winning creative. Requests it using an rpc if necessary.
            Throws an exception if an error occurs. """
            
        return creative  
       
    def run(self): 
        adgroups = self._get_adgroups()
    
        trace_logging.info(self.__class__.starting_message)
        
        trace_logging.info("Available adgroups are: %s" % adgroups)    
         
        filtered_adgroups = self._filter_adgroups(adgroups)
        
        trace_logging.info("Filtered adgroups are: %s" % filtered_adgroups)
    
        # TODO: Add in frequency capping.
    
        creatives = self.adunit_context.get_creatives_for_adgroups(filtered_adgroups)   
    
        filtered_creatives = self._filter_creatives(creatives)
    
        sorted_creatives = self._sort_creatives(filtered_creatives)
    
        for creative in sorted_creatives:
            try:
                return self._process_winner(creative) 
            except:
                pass
                                                    
class GteeHighBattle(Battle):  
    """ Runs the standard battle for all guaranteed campaigns. """
    
    starting_message = "Beginning guaranteed high campaigns..."         
    
    def _get_adgroups(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "gtee_high", all_adgroups)
        
class GteeBattle(Battle):  
    """ Runs the standard battle for all guaranteed campaigns. """

    starting_message = "Beginning guaranteed campaigns..."         

    def _get_adgroups(self):
        all_adgroups = self.adunit_context.adgroups 
        return filter(lambda ag: ag.campaign.campaign_type == "gtee", all_adgroups)        
        
    