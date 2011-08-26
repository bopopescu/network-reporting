from ad_server.auction.battles import (Battle, 
                                       GteeBattle, 
                                       GteeHighBattle,
                                       GteeLowBattle,
                                       PromoBattle,
                                       MarketplaceBattle, 
                                      )
                                      
def run(client_context, adunit_context):   
    """ Runs the auction, returns a creative and an updated list of 
        excluded_adgroup_keys """ 
    
    client_context.geo_predicates = geo_predicates_from_country_code(client_context.country_code)
                               
    # Run each of our battle levels in the appropriate order.
    battle_classes = [GteeHighBattle,
                      GteeBattle,
                      GteeLowBattle,
                      PromoBattle,
                      MarketplaceBattle,
                      # NetworkBattle,
                      # BackfillPromoBattle
                      ]                      
     
    # Return the first successful creative
    for BattleClass in battle_classes:                    
        battle = BattleClass(client_context, adunit_context)
        creative = battle.run()
        if creative: 
            return (creative, client_context.excluded_adgroup_keys)              

    # No battle found an eligble creative
    return (None, client_context.excluded_adgroup_keys)




def geo_predicates_from_country_code(country_code): 
    """ This desperately needs to be refactored. Three steps to happiness:
        1. Deprecate the idea of a 'geo_predicate'
        2. Start recording country, region, state and city information
        3. Tweak geo_filter to use the new fields
        """       
    if not country_code:
        return ["country_name=US","country_name=*"]
    else:
        return ["country_name=%s" % country_code, "country_name=*"]

    # TODO: Ask Nafis - is multiple country codes a real thing?

    #if only one geo_pred (it's a country) check to see if this country has multiple
    #possible codes.  If it does, get all of them and use them all
    # if len(country_tuple) == 1 and ACCEPTED_MULTI_COUNTRY.has_key(country_tuple[0]):
    #     geo_predicates = reduce(lambda x,y: x+y, [geo_predicates_for_rgeocode([country_tupleess]) for country_tupleess in ACCEPTED_MULTI_COUNTRY[country_tuple[0]]])       
    
    
    
    
    
    
