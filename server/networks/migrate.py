from datetime import date

from google.appengine.ext import db

from account.models import Account
from account.query_managers import AccountQueryManager

from advertiser.models import NetworkStates, \
        Campaign, \
        AdGroup, \
        Creative
from advertiser.query_managers import CampaignQueryManager, \
        AdGroupQueryManager, \
        CreativeQueryManager, \
        AdvertiserQueryManager

from publisher.models import AdUnit
from publisher.query_managers import PublisherQueryManager

from common.utils.helpers import get_all, put_all
from common.constants import NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION

CAMPAIGN_FIELD_EXCLUSION_LIST = ['account', 'network_type', 'network_state', \
        'show_login', 'name']
ADGROUP_FIELD_EXCLUSION_LIST = ['account', 'campaign', 'net_creative',
        'site_keys', 'active']
CREATIVE_FIELD_EXCLUSION_LIST = ['ad_group', 'account']

SKIP_THESE_ACCOUNTS = []

def create_creative(new_adgroup, adgroup, put_data):
    old_creative = []
    if adgroup.creatives:
        old_creative = adgroup._creatives[0]
        print "AdGroup Creatives"
        print [str(creative.key()) for creative in adgroup._creatives]

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

def migrate(accounts=None, put_data=False, get_all_from_db=True):
    if not accounts:
        accounts = get_all(Account)

    accounts_dict = {}
    for account in accounts:
        account._adunits = []
        account._campaigns = []
        accounts_dict[account.key()] = account

    if get_all_from_db:
        for adunit in get_all(AdUnit):
            if adunit._account in accounts_dict:
                accounts_dict[adunit._account]._adunits.append(adunit)

        campaigns_dict = {}
        for campaign in get_all(Campaign):
            campaign._adgroups = []
            campaigns_dict[campaign.key()] = campaign
            if campaign._account in accounts_dict:
                accounts_dict[campaign._account]._campaigns.append(campaign)

        adgroups_dict = {}
        for adgroup in get_all(AdGroup):
            adgroup._creatives = []
            adgroups_dict[adgroup.key()] = adgroup
            if adgroup._campaign in campaigns_dict:
                campaigns_dict[adgroup._campaign]._adgroups.append(adgroup)

        for creative in get_all(Creative):
            if creative._ad_group in adgroups_dict:
                adgroups_dict[creative._ad_group]._creatives.append(creative)


    for account in accounts[:10]:#len(accounts)/4]:
        if account.display_new_networks or str(account.key()) in \
                SKIP_THESE_ACCOUNTS:
            continue

        if get_all_from_db:
            adunits = account._adunits
        else:
            adunits = PublisherQueryManager.get_adunits_dict_for_account(
                    account).values()
            account._campaigns = AdvertiserQueryManager. \
                    get_objects_dict_for_account(account).values()

        old_network_campaigns = [campaign for campaign in account._campaigns
                if campaign.campaign_type == 'network' and
                campaign.network_state == NetworkStates.STANDARD_CAMPAIGN]

        networks = set()
        print
        print "Migrating account: " + account.emails[0]
        print "Got all account advertiser models from memcache"
        for campaign in old_network_campaigns:
            if campaign._adgroups:
                adgroup = campaign._adgroups[0]

                network = adgroup.network_type.replace('_native',
                        '').lower()
                print "migrating old campaign for " + network
                # make sure it's not a deprecated campaign
                if adgroup.network_type not in ('millennial', \
                        'admob') and network in NETWORKS:
                    if network in networks or 'custom' in network:
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

                    networks.add(network)

            # mark old campaign and adgroup as deleted
            campaign.deleted = True
            for old_adgroup in campaign._adgroups:
                old_adgroup.deleted = True

        if put_data:
            CampaignQueryManager.put(old_network_campaigns)
            AdGroupQueryManager.put([adgroup for campaign in
                old_network_campaigns for adgroup in campaign._adgroups])

            account.display_new_networks = True
            account.display_networks_message = True
            AccountQueryManager.put_accounts(account)

def undo(accounts, put_data=False):
    for account in accounts:
        campaigns = [campaign for campaign in
                AdvertiserQueryManager.get_objects_dict_for_account(account).
                values() if campaign.campaign_type == 'network' and
            campaign.network_state != NetworkStates.STANDARD_CAMPAIGN]

        creatives = []
        adgroups = []
        for campaign in campaigns:
            for adgroup in campaign._adgroups:
                adgroup.deleted = True
                adgroups.append(adgroup)
                for creative in adgroup._creatives:
                    creative.deleted = True
                    creatives.append(creative)
        if put_data:
            CreativeQueryManager.delete(creatives)
            AdGroupQueryManager.delete(adgroups)
            CampaignQueryManager.delete(campaigns)

