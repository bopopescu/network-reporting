from google.appengine.ext import db

from account.models import Account
from account.query_managers import AccountQueryManager

from advertiser.models import NetworkStates
from advertiser.query_managers import CampaignQueryManager, \
        AdGroupQueryManager, \
        CreativeQueryManager

from publisher.query_managers import AdUnitQueryManager

from common.constants import NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION

CAMPAIGN_FIELD_EXCLUSION_LIST = ['account', 'network_type', 'network_state', \
        'show_login']
ADGROUP_FIELD_EXCLUSION_LIST = ['account', 'campaign', 'net_creative']
CREATIVE_FIELD_EXCLUSION_LIST = ['ad_group', 'account']

accounts = [Account.get('agltb3B1Yi1pbmNyEAsSB0FjY291bnQYscSjDww')]

# TODO: figure out net creatives

def bulk_get(query, last_object):
    return query.filter('__key__ >', last_object).fetch(MAX)

def create_creative(new_adgroup, adgroup):
    html_data = None
    if new_adgroup.network_type in ('custom', 'custom_native'):
        html_data = adgroup.html_data
    # build default creative with custom_html data if custom or
    # none if anything else
    new_creative = new_adgroup.default_creative(html_data)
    # copy properties of old creative to new one
    for field in adgroup.net_creative.properties().iterkeys():
        if field not in CREATIVE_FIELD_EXCLUSION_LIST:
            try:
                setattr(new_creative, field, getattr(adgroup.net_creative,
                    field))
            except db.DerivedPropertyError:
                pass

    # new adgroup shouldn't have a creative if it does delete it
    if new_adgroup.net_creative:
        CreativeQueryManager.delete(new_adgroup.net_creative)

    # the creative should always have the same account as the new adgroup
    new_creative.account = new_adgroup.account
    #put the creative so we can reference it
    CreativeQueryManager.put(new_creative)
    # set new adgroup to reference the correct creative
    new_adgroup.net_creative = new_creative.key()

# TODO: exclude certain fields from getting copied over

for account in accounts:
    adunits = AdUnitQueryManager.get_adunits(account=account)
    networks = set()
    print
    print "Migrating account: " + account.emails[0]
    for campaign in CampaignQueryManager.get_network_campaigns(account):
        # TODO: hash on shared settings (advanced settings)
        network = campaign.adgroups[0].network_type.replace('_native',
                '').lower()
        if network in NETWORKS:
            if network in networks:
                print "creating a custom network campaign"
                # create custom campaign
                new_campaign = Campaign(account=account,
                        network_type=network,
                        network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN,
                        name=campaign.name)
            else:
                print "creating a default network campaign"
                # create defualt network campaign
                new_campaign = CampaignQueryManager. \
                        get_default_network_campaign(account, network)
            for field in campaign.properties().iterkeys():
                if field not in CAMPAIGN_FIELD_EXCLUSION_LIST:
                    setattr(new_campaign, field, getattr(campaign, field))

            for adunit in adunits:
                # copy old campaign adgroup properties to new campaign adgroup
                # properties
                new_adgroup = AdGroupQueryManager.get_network_adgroup(
                        new_campaign, adunit.key(), account.key())
                for field in campaign.adgroups[0].properties().iterkeys():
                    if field not in ADGROUP_FIELD_EXCLUSION_LIST:
                        setattr(new_adgroup, field, getattr(
                            campaign.adgroups[0], field))
                # create creative for the new adgroup
                create_creative(new_adgroup, campaign.adgroups[0])
                AdGroupQueryManager.put(new_adgroup)
            CampaignQueryManager.put(new_campaign)

            networks.add(campaign.network_type)
    account.display_new_networks = True
    AccountQueryManager.put_accounts(account)

