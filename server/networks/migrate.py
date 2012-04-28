from datetime import date

from google.appengine.ext import db

from account.models import Account
from account.query_managers import AccountQueryManager

from advertiser.models import NetworkStates, \
        Campaign
from advertiser.query_managers import CampaignQueryManager, \
        AdGroupQueryManager, \
        CreativeQueryManager, \
        AdvertiserQueryManager

from publisher.query_managers import PublisherQueryManager

from common.constants import NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION

CAMPAIGN_FIELD_EXCLUSION_LIST = ['account', 'network_type', 'network_state', \
        'show_login', 'name']
ADGROUP_FIELD_EXCLUSION_LIST = ['account', 'campaign', 'net_creative',
        'site_keys', 'active']
CREATIVE_FIELD_EXCLUSION_LIST = ['ad_group', 'account']

def create_creative(new_adgroup, adgroup, put_data):
    old_creative = []
    if adgroup.creatives:
        old_creative = adgroup.creatives[0]
        print "AdGroup Creatives"
        print [str(creative.key()) for creative in adgroup.creatives]

    html_data = None
    if new_adgroup.network_type in ('custom', 'custom_native'):
        html_data = old_creative.html_data
    # build default creative with custom_html data if custom or
    # none if anything else
    new_creative = new_adgroup.default_creative(html_data)
    # copy properties of old creative to new one
    if  old_creative:
        for field in old_creative.properties().iterkeys():
            if field not in CREATIVE_FIELD_EXCLUSION_LIST:
                try:
                    setattr(new_creative, field, getattr(old_creative, field))
                except db.DerivedPropertyError:
                    pass

    # new adgroup shouldn't have a creative if it does delete it
    if new_adgroup.net_creative and put_data:
        CreativeQueryManager.delete(new_adgroup.net_creative)

    # the creative should always have the same account as the new adgroup
    new_creative.account = new_adgroup.account
    if put_data:
        #put the creative so we can reference it
        CreativeQueryManager.put(new_creative)
        # set new adgroup to reference the correct creative
        new_adgroup.net_creative = new_creative.key()

def migrate(accounts, put_data=False):
    for account in accounts:
        adunits = PublisherQueryManager.get_adunits_dict_for_account(
                account).values()
        networks = set()
        print
        print "Migrating account: " + account.emails[0]
        old_network_campaigns = [campaign for campaign in
                AdvertiserQueryManager.get_objects_dict_for_account(account).
                values() if campaign.campaign_type == 'network' and
                campaign.network_state == NetworkStates.STANDARD_CAMPAIGN]
        print "Got all account advertiser models from memcache"
        for campaign in old_network_campaigns:
            adgroup = campaign.adgroups[0]
            if adgroup:
                network = adgroup.network_type.replace('_native',
                        '').lower()
                print "migrating old campaign for " + network
                if network in NETWORKS:
                    if network in networks:
                        print "creating a custom network campaign"
                        # create custom campaign
                        new_campaign = Campaign(account=account,
                                network_type=network,
                                network_state=NetworkStates. \
                                        CUSTOM_NETWORK_CAMPAIGN,
                                name=campaign.name)
                        # Must save so key exists
                        if put_data:
                            CampaignQueryManager.put(new_campaign)
                        else:
                            continue
                    else:
                        print "creating a default network campaign"
                        # create defualt network campaign
                        new_campaign = CampaignQueryManager. \
                                get_default_network_campaign(account, network)
                    for field in campaign.properties().iterkeys():
                        if field not in CAMPAIGN_FIELD_EXCLUSION_LIST:
                            setattr(new_campaign, field, getattr(campaign,
                                field))
                    new_campaign.transition_date = date.today()
                    new_campaign.old_campaign = campaign

                    new_adgroups = []
                    for adunit in adunits:
                        # copy old campaign adgroup properties to new
                        # campaign adgroup properties
                        new_adgroup = AdGroupQueryManager.get_network_adgroup(
                                new_campaign, adunit.key(), account.key())
                        for field in adgroup.properties().iterkeys():
                            if field not in ADGROUP_FIELD_EXCLUSION_LIST:
                                setattr(new_adgroup, field, getattr(
                                    adgroup, field))
                        # set wether adunit is active for this network campaign
                        new_adgroup.active = adunit.key() in adgroup.site_keys
                        # create creative for the new adgroup
                        create_creative(new_adgroup, adgroup, put_data)
                        new_adgroups.append(adgroup)

                    if put_data:
                        AdGroupQueryManager.put(new_adgroup)
                        CampaignQueryManager.put(new_campaign)

                        # mark old campaign and adgroup as paused
                        campaign.active = False
                        CampaignQueryManager.put(campaign)
                        for old_adgroup in campaign.adgroups:
                            old_adgroup.active = False
                        AdGroupQueryManager.put(campaign.adgroups)

                    networks.add(network)
        if put_data:
            account.display_new_networks = True
            AccountQueryManager.put_accounts(account)

def undo():
    for account in accounts:
        for campaign in CampaignQueryManager.get_network_campaigns(account,
                is_new=True):
            for adgroup in campaign.adgroups:
                db.delete(adgroup.net_creative)
                db.delete(adgroup)
            db.delete(campaign)

