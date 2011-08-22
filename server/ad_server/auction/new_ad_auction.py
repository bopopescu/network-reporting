
def run_auction(battle_context,
                adunit_context,   
                ):   
    """ Runs the auction, returns a creative and an updated list of 
        excluded_adgroup_keys """ 
    
    battle_context.geo_predicates = geo_predicates_for_rgeocode(battle_context.country_tuple)
    
    all_adgroups = adunit_context.adgroups 
                               
    # Run each of our battles in the appropriate order.
    battle_classes = [GteeHighBattle,
                      GteeBattle,
                      GteeLowBattle,
                      PromoBattle,
                      MarketplaceBattle,
                      NetworkBattle,
                      BackfillPromoBattle]                      
     
    # Return the first successful creative
    for BattleClass in battle_classes:
        battle = BattleClass(battle_context, adunit_context)
        creative = battle.run()
        if creative: 
            return (creative, battle_context.excluded_adgroup_keys)              

    # No battle found an eligble creative
    return (None, battle_context.excluded_adgroup_keys)




def geo_predicates_for_rgeocode(country_tuple): 
    """ This desperately needs to be refactored. Three steps to happiness:
        1. Deprecate the idea of a 'geo_predicate'
        2. Start recording country, region, state and city information
        3. Tweak geo_filter to use the new fields
        """       
    r = country_tuple
    # r = [US, CA SF] or []
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # TODO: DEFAULT COUNTRY SHOULD NOT BE US!!!!!!!
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if len(r) == 0:
        return ["country_name=US","country_name=*"] # ["country_name"=*] or ["country_name=US] ["country_name="CD"]
    elif len(r) == 1:
        return ["country_name=%s" % r[0], "country_name=*"]
    elif len(r) == 2:
        return ["region_name=%s,country_name=%s" % (r[0], r[1]),
              "country_name=%s" % r[1],
              "country_name=*"]
    elif len(r) == 3:
        return ["city_name=%s,region_name=%s,country_name=%s" % (r[0], r[1], r[2]),
              "region_name=%s,country_name=%s" % (r[1], r[2]),
              "country_name=%s" % r[2],
              "country_name=*"]         
               
    #if only one geo_pred (it's a country) check to see if this country has multiple
    #possible codes.  If it does, get all of them and use them all
    if len(country_tuple) == 1 and ACCEPTED_MULTI_COUNTRY.has_key(country_tuple[0]):
        geo_predicates = reduce(lambda x,y: x+y, [AdAuction.geo_predicates_for_rgeocode([country_tupleess]) for country_tupleess in ACCEPTED_MULTI_COUNTRY[country_tuple[0]]])