from account.models import MarketPlaceConfig, NetworkConfig
from account.query_managers import AccountQueryManager
from advertiser.models import (Campaign, AdGroup, Creative, MarketplaceCreative,
                               HtmlCreative, NetworkStates)
from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)
from common.constants import NETWORKS
from publisher.models import App, AdUnit
from publisher.query_managers import AdUnitQueryManager
from registration.models import RegistrationManager


DEFAULT_HTML = 'html_data1'


def _generate_model_instance(model, put, defaults, **kwargs):
    defaults.update(kwargs)
    model_instance = model(**defaults)
    if put:
        model_instance.put()
    return model_instance


def generate_account(username, password):
    # Create a user and profile based on passed-in credentials.
    manager = RegistrationManager()
    user = manager.create_active_user(send_email=False, username=username,
                                      password=password, email=username)
    manager.create_profile(user)

    # Create an account for this user. Mark it as active and as using new-style
    # networks.
    account = AccountQueryManager().get_current_account(user=user)
    account.active = True
    account.display_new_networks = True

    account.put()

    # Since this is a new account, it needs marketplace and network configs.
    marketplace_config = MarketPlaceConfig()
    marketplace_config.put()
    account.marketplace_config = marketplace_config

    network_config = NetworkConfig(account=account)
    network_config.put()
    account.network_config = network_config

    # This account also needs a default marketplace campaign.
    marketplace_campaign = CampaignQueryManager.get_marketplace(account)
    marketplace_campaign.put()

    account.put()

    return account


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
        'campaign_type': 'order',
    }
    return _generate_model_instance(Campaign, put, defaults, **kwargs)


def generate_network_campaign(account, network_type, put=False, **kwargs):
    """Creates a network campaign along with any necessary adgroups/creatives.

    NOTE: argument apps needs adunits attached.

    Author: Andrew He
    """
    campaigns = CampaignQueryManager.get_network_campaigns(account,
        network_type=network_type)
    # Generate the campaign object.
    if network_type in ('custom', 'custom_native') or campaigns:
        campaign = Campaign(name=NETWORKS[network_type],
                            campaign_type='network',
                            network_type=network_type,
                            network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN,
                            account=account)
    else:
        campaign = CampaignQueryManager.get_default_network_campaign(
            account, network_type)

    if not put:
        return campaign

    CampaignQueryManager.put(campaign)

    # Generate one adgroup per adunit.
    for adunit in AdUnitQueryManager.get_adunits(account=account):
        adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                adunit.key(), account.key())
        AdGroupQueryManager.put(adgroup)

        # Generate the creative for this adgroup.
        if network_type in ('custom', 'custom_native'):
            creative = adgroup.default_creative(custom_html=DEFAULT_HTML)
        else:
            creative = adgroup.default_creative()
        creative.account = account
        CreativeQueryManager.put(creative)

    return campaign


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
