def build_marketplace_dict(adunit, kws, udid, ua, ll, ip, adunit_context):
        app = adunit.app_key
        ret =  dict(adunit_id = str(adunit.key()),
                    format = adunit.format,
                    mopub_id = udid,
                    user_keywords = None,
                    keywords = kws,
                    latlng = ll,
                    user_agent = ua,
                    ip = ip,
                    app_id = str(app.key()),
                    app_name = app.name,
                    # I think this is right?
                    app_domain = app.package if app.app_type in ('iphone', 'ipad') else None,
                    pub_id = str(app.account.key()),
                    pub_name = app.account.company,
                    pub_domain = app.account.domain,
                    categories = [app.primary_category, app.secondary_category],
                    #categories = app.categories,
                    app_bundle = app.package if app.app_type == 'android' else None,
                    # These return 0 if interstitial or w/e, don't return 0 just None
                    width = adunit.get_width() or None,
                    height = adunit.get_height() or None,
                    )
        none_keys = []
        for k,v in ret.iteritems():
            if v is None:
                none_keys.append(k)
        for key in none_keys:
            del(ret[key])
        return ret

