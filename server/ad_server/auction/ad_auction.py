from ad_server.auction.battles import (GteeBattle,
                                       GteeHighBattle,
                                       GteeLowBattle,
                                       PromoBattle,
                                       MarketplaceBattle,
                                       NetworkBattle,
                                       BackfillPromoBattle
                                      )

def run(client_context, adunit_context, MarketplaceBattle=MarketplaceBattle):
    """ Runs the auction, returns a creative and an updated list of
        excluded_adgroup_keys. Pass in MarketplaceBattle as kwarg
        for testing purposes. """

    client_context.geo_predicates = geo_predicates_from_country_code(client_context.country_code)

    # Run each of our battle levels in the appropriate order.
    gtee_and_promo_battle_classes = [GteeHighBattle,
                                     GteeBattle,
                                     GteeLowBattle,
                                     PromoBattle,
                                     ]
    # Run Gtee and Promo Battles. Return the first successful creative
    for BattleClass in gtee_and_promo_battle_classes:
        battle = BattleClass(client_context, adunit_context)
        creative = battle.run()
        if creative:
            return (creative, client_context.excluded_adgroup_keys)


    # Run the MarketplaceBattle, and then pass the winning bid into the NetworkBattle
    marketplace_battle = MarketplaceBattle(client_context, adunit_context)
    marketplace_creative = marketplace_battle.run()    
    
    if marketplace_creative:
        marketplace_cpm = marketplace_creative.adgroup.bid    
    else:
        marketplace_cpm = 0.0
    
    print marketplace_cpm 
    # Run NetworkBattle, we pass in a minimum cpm that the networks must beat    
    network_battle = NetworkBattle(client_context,
                                   adunit_context,
                                   min_cpm=marketplace_cpm)
    network_creative = network_battle.run()    
    print network_creative
    if network_creative:
        return (network_creative, client_context.excluded_adgroup_keys)                   
    # If the networks couldn't beat the marketplace bid, return marketplace
    elif marketplace_creative:
        return (marketplace_creative, client_context.excluded_adgroup_keys)


    # Finally run backfill Promo
    backfill_battle = BackfillPromoBattle(client_context, adunit_context)
    backfill_creative = backfill_battle.run()    

    # If the networks couldn't beat the marketplace bid, return marketplace
    if backfill_creative:
        return (backfill_creative, client_context.excluded_adgroup_keys)

    # No battle found an eligible creative
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


