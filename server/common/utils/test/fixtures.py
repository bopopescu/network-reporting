from account.models import NetworkConfig
from advertiser.models import (Campaign, AdGroup, Creative, MarketplaceCreative,
                               HtmlCreative)
from publisher.models import App, AdUnit


def _generate_model_instance(model, put, defaults, **kwargs):
    defaults.update(kwargs)
    model_instance = model(**defaults)
    if put:
        model_instance.put()
    return model_instance


def generate_network_config(account, put=False, **kwargs):
    defaults = {
        'account': account,
    }
    return _generate_model_instance(NetworkConfig, put, defaults, **kwargs)


def generate_app(account, put=False, **kwargs):
    defaults = {
        'account': account,
        'name': 'Book App',
        'app_type': 'iphone',
        'primary_category': 'books',
    }
    return _generate_model_instance(App, put, defaults, **kwargs)


def generate_adunit(account, app, put=False, **kwargs):
    defaults = {
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
    return _generate_model_instance(AdUnit, put, defaults, **kwargs)


def generate_campaign(account, put=False, **kwargs):
    defaults = {
        'account': account,
        'name': 'Test Campaign',
        'campaign_type': 'gtee',
    }
    return _generate_model_instance(Campaign, put, defaults, **kwargs)


def generate_adgroup(account, campaign, put=False, **kwargs):
    defaults = {
        'account': account,
        'campaign': campaign,
    }
    return _generate_model_instance(AdGroup, put, defaults, **kwargs)


def generate_creative(account, adgroup, put=False, **kwargs):
    defaults = {
        'account': account,
        'adgroup': adgroup,
    }
    return _generate_model_instance(Creative, put, defaults, **kwargs)


def generate_marketplace_creative(account, adgroup, put=False, **kwargs):
    defaults = {
        'account': account,
        'ad_group': adgroup,
    }
    return _generate_model_instance(MarketplaceCreative, put, defaults, **kwargs)


def generate_html_creative(account, adgroup, put=False, **kwargs):
    defaults = {
        'account': account,
        'ad_group': adgroup,
    }
    return _generate_model_instance(HtmlCreative, put, defaults, **kwargs)
