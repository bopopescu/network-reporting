from google.appengine.ext import db

from advertiser.models import NetworkStates
from advertiser.query_managers import CampaignQueryManager, \
        AdGroupQueryManager, \
        CreativeQueryManager

from publisher.query_managers import AdUnitQueryManager

from common.constants import NETWORKS


accounts = []

# TODO: figure out net creatives

def bulk_get(query, last_object):
    return query.filter('__key__ >', last_object).fetch(MAX)

for account in accounts:
    adunits = AdUnitQueryManager.get_adunits(account=account)
    networks = set()
    for campaign in CampaignQueryManager.get_network_campaigns(account):
        # TODO: hash on shared settings (advanced settings)
        if campaign.network_type in NETWORKS:
            if campaign.network_type in networks:
                # create custom campaign
                new_campaign = Campaign(account=account,
                        network_type=network,
                        network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN,
                        name=campaign.name)
            else:
                # create defualt network campaign
                new_campaign = CampaignQueryManager. \
                        get_default_network_campaign(account,
                                campaign.network_type)
            for field in campaign.properties().iterkeys():
                setattr(new_campaign, field, getattr(campaign, field))

            for adunit in adunits:
                # copy old campaign adgroup properties to new campaign adgroup
                # properties
                new_adgroup = AdGroupQueryManager.get_network_adgroup(
                        new_campaign, adunit.key(), account.key())
                for field in campaign.adgroup.properties().iterkeys():
                    setattr(new_adgroup, field, getattr(camaign.adgroup,
                            field))
                # create creative for the new adgroup
                create_creative(new_adgroup, campaign.adgroup)
                AdGroupQueryManager.put(new_adgroup)
            CampaignQueryManager.put(new_campaign)

            networks.add(campaign.network_type)

def create_creative(new_adgroup, adgroup):
    html_data = None
    if new_adgroup.network_type in ('custom', 'custom_native'):
        html_data = adgroup.html_data
    # build default creative with custom_html data if custom or
    # none if anything else
    new_creative = new_adgroup.default_creative(html_data)
    # copy properties of old creative to new one
    for field in adgroup.creative.properties().iterkeys():
        setattr(new_creative, field, getattr(adgroup.creative, field))

    # new adgroup shouldn't have a creative if it does delete it
    if new_adgroup.net_creative:
        CreativeQueryManager.delete(new_adgroup.net_creative)

    # the creative should always have the same account as the new adgroup
    new_creative.account = new_adgroup.account
    #put the creative so we can reference it
    CreativeQueryManager.put(new_creative)
    # set new adgroup to reference the correct creative
    new_adgroup.net_creative = new_creative.key()

