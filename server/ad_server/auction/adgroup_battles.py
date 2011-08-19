class AdgroupBattle(object):
    """ Determines the best adgroup from a subset of adgroups """  
    
    FILTERS = (exclude_filter(excluded_adgroups),
               active_filter(), 
               lat_lon_filter(ll),
               kw_filter(keywords), 
               geo_filter(geo_predicates), 
               device_filter(device_predicates),
               os_filter(user_agent),
               budget_filter())
    
    starting_message = "Beginning priority level x ..."
    
    @classmethod
    def run_battle(cls, adgroups, excluded_adgroup_keys, **kwargs): 
        """ Returns a creative with a bid if one exists 
            Modifies the list of excluded adgroup_keys""" 
            
            
        filtered_adgroups = filter(mega_filter(*cls.FILTERS), all_ad_groups)
        for (func, warn, removed_adgroup_list) in ALL_FILTERS:
            trace_logging.info(warn % ", ".join([a.name.encode('utf8') for a in removed_adgroup_list]))   
         
        
        # TODO: Add in frequency capping.
        
        
        filtered_adgroups.sort
        
        
         