import logging 
###############################
# BASIC FILTERS
#
# --- Each filter function is a function which takes some arguments (or none) necessary 
#       for the filter to work its magic. log_mesg is the message that will be logged 
#       for the associated objects that eval'd to false.
# --- ALL FILTER GENERATOR FUNCTIONS MUST RETURN ( filter_function, log_mesg, [] )
# --- The empty list is the list that will contain all elt's for which the 
#       filter_function returned False
###############################

def budget_filter():
    log_mesg = "Removed due to being over budget: %s"
    def real_filter( a ):
        return not ( a.budget is None or a.campaign.delivery_counter.count < a.budget )
        # return budget_service.process(a.campaign.key, a.bid, a.campaign)
    return ( real_filter, log_mesg, [] )

def active_filter():
    log_mesg = "Removed due to inactivity: %s"
    def real_filter( a ):
        return not ( a.campaign.active and ( a.campaign.start_date  >= SiteStats.today() if a.campaign.start_date else True ) and ( SiteStats.today() <= a.campaign.end_date if a.campaign.end_date else True ) )
    return ( real_filter, log_mesg, [] )

def kw_filter( keywords ):
    log_mesg = "Removed due to keyword mismatch: %s"
    def real_filter( a ):
        return not ( not a.keywords or set( keywords ).intersection( a.keywords ) > set() )
    return ( real_filter, log_mesg, [] )

def geo_filter( geo_preds ):
    log_mesg = "Removed due to geo mismatch: %s"
    def real_filter( a ):
        return not ( set( geo_preds ).intersection( a.geographic_predicates ) > set() )
    return ( real_filter, log_mesg, [] )

def device_filter( dev_preds ):
    log_mesg = "Removed due to device mismatch: %s"
    def real_filter( a ):
        return  not ( set( dev_preds ).intersection( a.device_predicates ) > set() )
    return ( real_filter, log_mesg, [] )

def mega_filter( *filters ): 
    def actual_filter( a ):
        for ( f, msg, lst ) in filters:
            if f( a ):
                lst.append( a )
                return False
        return True
    return actual_filter

######################################
#
# Creative filters
#
######################################

def format_filter( format ):
    log_mesg = "Removed due to format mismatch, expected " + str( format ) + ": %s"
    def real_filter( a ):
        if not a.format: 
            return False
        return not a.format == format
    return ( real_filter, log_mesg, [] )

def exclude_filter( excl_params ):
    log_mesg = "Removed due to exclusion parameters: %s"
    # NOTE: we are excluding on ad type not the creative id
    def real_filter( a ):
        return a.ad_type in excl_params 
    return ( real_filter, log_mesg, [] )

def ecpm_filter( winning_ecpm ):
    log_mesg = "Removed due to being a loser: %s"
    def real_filter( a ):
        return not a.e_cpm() >= winning_ecpm
    return ( real_filter, log_mesg, [] )

##############################################
#
#   FREQUENCY FILTERS
#
##############################################


def freq_filter( type, key_func, udid, now, frq_dict ):
    """Function for constructing a frequency filter
    Super generic, made this way since all frequencies are just
     -verify frequency cap, if yes make sure we're not over it, otherwise carry on
    so I just made a way to generate them"""
    
    log_mesg = "Removed due to " + type + " frequency cap: %s"
    def real_filter( a ):
        a_key = key_func( udid, now, a.key() )
        #This is why all frequency cap attributes must follow the same naming convention, otherwise this
        #trick doesn't work
        try:
            frq_cap = getattr( a, '%s_frequency_cap' % type ) 
        except:
            frq_cap = 0

        if frq_cap and ( a_key in frq_dict ):
            imp_cnt = int( frq_dict[ a_key ] )
        else:
            imp_cnt = 0
        #Log the current counts and cap
        logging.warning( "%s imps: %s, freq cap: %d" % ( type.title(), imp_cnt, frq_cap ) )
        return not ( not frq_cap or imp_cnt < frq_cap )
    return ( real_filter, log_mesg, [] )

#this is identical to mega_filter except it logs the adgroup 
def all_freq_filter( *filters ):
    def actual_filter( a ):
        #print the adgroup title so the counts/cap printing in the acutal filter don't confuse things
        logging.warning( "Adgroup: %s" % a )
        for f, msg, lst in filters:
            if f( a ):
                lst.append( a )
                return False
        return True
    return actual_filter


###############
# End filters
###############