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

# NOTE: vrubba and withbuddies must be manually migrated
SKIP_THESE_ACCOUNTS = set(['agltb3B1Yi1pbmNyEAsSB0FjY291bnQYvaXlBQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYu_LVEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYnsixEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYkfaLAQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYrpTsEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY_pG0Egw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYhLGNEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYr86zEAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYj7WVCQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYoKWrEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYsM68EQw', 'agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTEwODY0MDIzODQyNDcyMzQ5NzE1MQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY69isEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYxdaQAgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYirCdAgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYoa_DCgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8LrPDww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYwKvhAQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYt_XHEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1eKYDAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYjc6tEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYgNu-EQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYornTEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYn6KDEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYx8XfEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY76O-Agw', 'agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTEwMTEyNzQwOTg4Njk0NTM4Njc4NAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYy7CVEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY4f3tCAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYoauPEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY9dvjEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8IbxEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYya6pEAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYr4TkBww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY4_rnEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY4qrqCAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY_aGNEgw', 'agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTExMzgyNjUxOTkxNzc5MjcwNTc5NAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8IPYEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY-ICiEww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8_mQEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYlNGhDww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYlvriEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYiZKkEww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYgt3DEAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY49yLBQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYoP_EAQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYzKOtEAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYm4SPEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYwbjaCQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY_uW-EQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYz_PxDgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY09GeAQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY4d60DQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYsY69Egw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY0KzNEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1Z6cEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYje6JCww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYua6oBQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYyonACAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYhs2wEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYn7XSEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY57KfAgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY-afzEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYo8qPEgw', 'agltb3B1Yi1pbmNyDwsSB0FjY291bnQY8NdTDA', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY7cCnEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYlK6YEww', 'agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTExNDcwNTU3MjUxMzE0ODc3NzM2OAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY9ZjDDww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8YHEBQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY0_iuDAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY4bDjBww', 'agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTEwODI5NTY1MzM0NzIzMjM1NjgyOQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYs7znEgw', 'agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTExMjcxMTI4Nzk2OTE1NTEwODQ2Ngw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYncfIBww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYzKSTEQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYh6iMCww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYzsrQEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY79yPDww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYpomQCgw', 'agltb3B1Yi1pbmNyDwsSB0FjY291bnQYmbBzDA', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY-aOuEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY_ubpBAw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYzdeVEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY7-i2Agw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYq_imDww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYmrnOEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY18uyCww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYqdXOBww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1dqREww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY5auRDgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY-67GBQw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYvNujEww', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY9q6TEgw', 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQYubGGDww'])

def create_creative(new_adgroup, old_adgroup):
    old_creative = []
    if old_adgroup.creatives:
        old_creative = old_adgroup._creatives[0]
        print "AdGroup Creatives"
        print [str(creative.key()) for creative in old_adgroup._creatives]

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

    # the creative should always have the same account as the new adgroup
    new_creative.account = new_adgroup.account

    # return the new_creative
    return new_creative

def migrate(accounts=None, put_data=False, get_all_from_db=True):
    if not accounts:
        print "Getting all accounts"
        accounts = get_all(Account)

    accounts_dict = {}
    for account in accounts:
        account._adunits = []
        account._campaigns = []
        accounts_dict[account.key()] = account

    if get_all_from_db:
        print "Getting all adunits"
        for adunit in get_all(AdUnit):
            if adunit._account in accounts_dict:
                accounts_dict[adunit._account]._adunits.append(adunit)

        print "Getting all campaigns"
        campaigns_dict = {}
        for campaign in get_all(Campaign):
            campaign._adgroups = []
            campaigns_dict[campaign.key()] = campaign
            if campaign._account in accounts_dict:
                accounts_dict[campaign._account]._campaigns.append(campaign)

        print "Getting all adgroups"
        adgroups_dict = {}
        for adgroup in get_all(AdGroup):
            adgroup._creatives = []
            adgroups_dict[adgroup.key()] = adgroup
            if adgroup._campaign in campaigns_dict:
                campaigns_dict[adgroup._campaign]._adgroups.append(adgroup)

        print "Getting all creatives"
        for creative in get_all(Creative):
            if creative._ad_group in adgroups_dict:
                adgroups_dict[creative._ad_group]._creatives.append(creative)


    new_campaigns = []
    old_campaigns = []
    migrated_adgroups = []
    old_adgroups = []
    print
    print "LOOPING THROUGH ACCOUNTS TO SETUP CAMPAIGNS"
    print
    for account in accounts[:10]:#len(accounts)/4]:
        if account.display_new_networks or str(account.key()) in \
                SKIP_THESE_ACCOUNTS:
            print "Skipping account: %s" % account.emails[0]
            continue

        if not get_all_from_db:
            print "Getting all account advertiser models from memcache"
            account._campaigns = AdvertiserQueryManager. \
                    get_objects_dict_for_account(account).values()

        old_campaigns_for_account = [campaign for campaign in account._campaigns
                if campaign.campaign_type == 'network' and
                campaign.network_state == NetworkStates.STANDARD_CAMPAIGN and
                campaign.deleted == False]

        networks = set()
        print
        print "Migrating account: " + account.emails[0]
        for old_campaign in old_campaigns_for_account:
            if old_campaign._adgroups:
                # One to one mapping between old network campaigns and adgroups
                old_adgroup = old_campaign._adgroups[0]

                network = old_adgroup.network_type.replace('_native',
                        '').lower()
                # make sure it's not a deprecated campaign
                if old_adgroup.network_type not in ('millennial', \
                        'admob') and network in NETWORKS:
                    print "migrating old campaign for " + network
                    if network in networks or 'custom' in network:
                        print "creating a custom network campaign"
                        # create custom campaign
                        new_campaign = Campaign(account=account,
                                network_type=network,
                                network_state=NetworkStates. \
                                        CUSTOM_NETWORK_CAMPAIGN,
                                name=campaign.name)
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

                    new_campaigns.append(new_campaign)
                    migrated_adgroups(old_adgroup)

                    networks.add(network)
                else:
                    print "Skipping deprecated campaign: %s" % \
                            old_adgroup.network_type

            # mark old campaign and adgroup as deleted
            campaign.deleted = True
            for old_adgroup in campaign._adgroups:
                old_adgroup.deleted = True
                old_adgroups.append(old_adgroup)

            old_campaigns.append(campaign)


    print "Saving all campaigns"
    if put_data:
        put_all(new_campaigns)


    print
    print "LOOPING THROUGH ACCOUNTS TO SETUP ADGROUPS AND CREATIVES"
    print
    new_adgroups = []
    new_creatives = []
    affected_accounts = []
    for account in accounts[:10]:#len(accounts)/4]:
        if account.display_new_networks or str(account.key()) in \
                SKIP_THESE_ACCOUNTS:
            continue

        if get_all_from_db:
            adunits = account._adunits
        else:
            adunits = PublisherQueryManager.get_adunits_dict_for_account(
                    account).values()

        for new_campaign, old_adgroup in zip(new_campaigns, migrated_adgroups):
            if not put_data and new_campaign.network_type == \
                    NetworkStates.CUSTOM_NETWORK_CAMPAIGN:
                continue

            for adunit in adunits:
                # copy old campaign adgroup properties to new
                # campaign adgroup properties
                new_adgroup = AdGroupQueryManager.get_network_adgroup(
                        new_campaign, adunit.key(), account.key())
                for field in old_adgroup.properties().iterkeys():
                    if field not in ADGROUP_FIELD_EXCLUSION_LIST:
                        setattr(new_adgroup, field, getattr(
                            old_adgroup, field))
                # set wether adunit is active for this network campaign
                new_adgroup.active = adunit.key() in old_adgroup.site_keys
                # create creative for the new adgroup
                new_creatives.append(create_creative(new_adgroup,
                    old_adgroup))
                new_adgroups.append(new_adgroup)

        if not account.display_new_networks:
            affected_accounts.append(account)

        account.display_new_networks = True
        account.display_networks_message = True

    print "Saving all account data"
    if put_data:
        print "Saving old campaigns"
        put_all(old_campaigns)
        print "Saving old and new adgroups"
        put_all(old_adgroups + new_adgroups)
        print "Saving new creatives"
        put_all(new_creatives)

        print "Saving accounts"
        put_all(accounts[:10])

        print "Flushing the cache"
        affected_account_keys = [account.key() for account in affected_accounts]
        AdvertiserQueryManager.memcache_flush_entities_for_account_keys(
                affected_account_keys, Campaign)
        AdvertiserQueryManager.memcache_flush_entities_for_account_keys(
                affected_account_keys, AdGroup)
        AdvertiserQueryManager.memcache_flush_entities_for_account_keys(
                affected_account_keys, Creative)

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

