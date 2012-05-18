from advertiser.models import Campaign, AdGroup
from publisher.models import App, AdUnit


def generate_app(account, **kwargs):
    app_dict = {
        'account': account,
        'name': 'Book App',
        'app_type': 'iphone',
        'primary_category': 'books',
    }
    app_dict.update(kwargs)
    app = App(**app_dict)
    app.put()
    return app


def generate_adunit(account, app, **kwargs):
    adunit_dict = {
        'app_key': app,
        'account': account,
        'name': 'Banner Ad',
        'device_format': 'phone',
        'format': '320x50',
        'ad_type': None,
        'color_border': '336699',
        'color_bg': 'FFFFFF',
        'color_link': '0000FF',
        'color_text': '000000',
        'color_url': '008000',
    }
    adunit_dict.update(kwargs)
    adunit = AdUnit(**adunit_dict)
    adunit.put()
    return adunit


def generate_campaign(account, **kwargs):
    campaign_dict = {
        'account': account,
        'name': 'Test Campaign',
        'campaign_type': 'gtee',
    }
    campaign_dict.update(kwargs)
    campaign = Campaign(**campaign_dict)
    campaign.put()
    return campaign


def generate_adgroup(account, campaign, **kwargs):
    adgroup_dict = {
        'account': account,
        'campaign': campaign,
    }
    adgroup_dict.update(kwargs)
    adgroup = AdGroup(**adgroup_dict)
    adgroup.put()
    return adgroup


def default_app_dict(account, **kwargs):
    app_dict = {
        'account': account,
        'deleted': False,
        'name': u'Book App',
        'global_id': None,
        'adsense_app_name': None,
        'adsense_app_id': None,
        'admob_bgcolor': None,
        'admob_textcolor': None,
        'app_type': u'iphone',
        'description': None,
        'url': None,
        'package': None,
        'categories': [],
        'icon_blob': None,
        'image_serve_url': None,
        'jumptap_app_id': None,
        'millennial_app_id': None,
        'exchange_creative': None,
        'experimental_fraction': 0.0,
        'network_config': None,
        'primary_category': u'books',
        'secondary_category': None,
        'use_proxy_bids': True,
        'force_marketplace': True,
    }

    app_dict.update(kwargs)
    return app_dict


def default_adunit_dict(account, app, **kwargs):
    adunit_dict = {
        'name': u'Banner Ad',
        'description': None,
        'ad_type': None,
        'custom_width': None,
        'custom_height': None,
        'format': u'320x50',
        'app_key': app,
        'device_format': u'phone',
        'refresh_interval': 0,
        'account': account,
        'adsense_channel_id': None,
        'url': None,
        'resizable': False,
        'landscape': False,
        'deleted': False,
        'jumptap_site_id': None,
        'millennial_site_id': None,
        'keywords': None,
        'animation_type': u'0',
        'color_border': u'336699',
        'color_bg': u'FFFFFF',
        'color_link': u'0000FF',
        'color_text': u'000000',
        'color_url': u'008000',
        'network_config': None,
    }

    adunit_dict.update(kwargs)
    return adunit_dict
