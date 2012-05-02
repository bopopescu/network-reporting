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

def create_creative(new_adgroup, adgroup, put_data):
    old_creative = []
    if adgroup._creatives:
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

    # the creative should always have the same account as the new adgroup
    new_creative.account = new_adgroup.account

    # return the new_creative
    return new_creative

def migrate(accounts=None, put_data=False):
    if not accounts:
        accounts = get_all(Account)

    for account in accounts[:10]:#len(accounts)/4]:
        if account.display_new_networks or str(account.key()) in \
                SKIP_THESE_ACCOUNTS:
            continue

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
        new_campaigns = []
        new_adgroups = []
        new_creatives = []
        for campaign in old_network_campaigns:
            if campaign._adgroups:
                adgroup = campaign._adgroups[0]

                network = adgroup.network_type.replace('_native',
                        '').lower()
                print "migrating old campaign for " + network
                if adgroup.network_type not in ('millennial', \
                        'admob') and network in NETWORKS:
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
                            print "Saving custom capaign: %s" % \
                                    new_campaign.key()
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
                        new_creatives.append(create_creative(new_adgroup,
                            adgroup, put_data))
                        new_adgroups.append(adgroup)

                    new_campaigns.append(new_campaign)

                    networks.add(network)

            # mark old campaign and adgroup as deleted
            campaign.deleted = True
            for old_adgroup in campaign._adgroups:
                old_adgroup.deleted = True

        print "Saving account data"
        account.display_new_networks = True
        account.display_networks_message = True
        if put_data:
            CampaignQueryManager.put(old_network_campaigns + new_campaigns)
            AdGroupQueryManager.put([adgroup for campaign in
                old_network_campaigns for adgroup in campaign._adgroups] +
                new_adgroups)
            CreativeQueryManager.put(new_creatives)

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

