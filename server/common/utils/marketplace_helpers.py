def build_marketplace_dict(adunit, kws, udid, ua, ll, ip, adunit_context, country):
        app = adunit.app_key
        adunit_width, adunit_height = get_width_and_height(adunit)
        if app.primary_category == "not_selected":
            primary_category = None
        else:
            primary_category = app.primary_category
        if app.secondary_category == "not_selected":
            secondary_category = None
        else:
            secondary_category = app.secondary_category
        ret =  dict(adunit_id = str(adunit.key()),
                    format = adunit.format,
                    mopub_id = udid,
                    user_keywords = None,
                    keywords = kws,
                    latlng = ll,
                    user_agent = ua,
                    ip = ip,
                    app_id = str(app.key()),
                    global_app_id = app.global_id or None,
                    app_name = app.name,
                    #app_domain = app.package if app.app_type in ('iphone', 'ipad') else None,
                    pub_id = str(app.account.key()),
                    pub_name = app.account.company,
                    pub_domain = app.account.domain,
                    pub_rev_share = app.account.marketplace_config.rev_share,
                    price_floor = app.account.marketplace_config.price_floor,
                    primary_category = primary_category, 
                    secondary_category = secondary_category,
                    #app_bundle = app.package if app.app_type == 'android' else None,
                    # These return 0 if interstitial or w/e, don't return 0 just None
                    width = adunit_width,
                    height = adunit_height,
                    paid = 0,
                    country = country,
                    )
        none_keys = []
        for k,v in ret.iteritems():
            if v is None:
                none_keys.append(k)
        for key in none_keys:
            del(ret[key])
        return ret

def get_width_and_height(adunit):
    if adunit.format == "full" and not adunit.landscape:
        adunit_width = 320
        adunit_height = 480
    elif adunit.format == "full" and adunit.landscape:
        adunit_width = 480
        adunit_height = 320
    elif adunit.format == "full_tablet" and not adunit.landscape:
        adunit_width = 768
        adunit_height = 1024
    elif adunit.format == "full_tablet" and adunit.landscape:
        adunit_width = 1024
        adunit_height = 768
    else:
        adunit_width = adunit.get_width()
        adunit_height = adunit.get_height()
    return adunit_width, adunit_height