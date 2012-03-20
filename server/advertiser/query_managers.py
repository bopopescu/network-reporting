import random

from google.appengine.api import memcache
from google.appengine.ext import db

from common.utils.query_managers import QueryManager, CachedQueryManager
from common.utils.decorators import wraps_first_arg

from common.constants import CAMPAIGN_LEVELS

from advertiser.models import Campaign
from advertiser.models import AdGroup
from advertiser.models import Creative, TextCreative, \
                              TextAndTileCreative, \
                              HtmlCreative,\
                              ImageCreative, \
                              NetworkStates

from publisher.models import App, AdUnit
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
from budget.query_managers import BudgetQueryManager

import copy

from common.constants import MAX_OBJECTS

NAMESPACE = None

MAX_ALLOWABLE_QUERIES = 30

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class CampaignQueryManager(QueryManager):
    Model = Campaign

    @classmethod
    def get_campaigns_by_types(cls, account, types):
        campaigns = cls.Model.all().filter('account =', account)\
                                   .filter('campaign_type IN', types)\
                                   .filter('deleted =', False)
        return campaigns

    @classmethod
    def get_network_campaign(cls, account, network_type):
        network = cls.Model.all().filter('campaign_type =', 'network') \
                      .filter('deleted =',False) \
                      .filter('account =',account) \
                      .filter('network_type =', network_type).get()
        return network

    @classmethod
    def get_network_campaigns(cls, account):
        networks = cls.Model.all().filter('campaign_type =', 'network')\
                      .filter('deleted =',False)\
                      .filter('account =',account)
        return networks

    @classmethod
    def get_marketplace(cls, account, from_db=False):
        """
        Returns the only campaign that can belong to this account.
        The magic of key_names allows us to
        avoid getting the object from the db because
        all the information is a function of the account itself.

        Note: it is the API consumer's responsiblity to actually
        save this object with the put method of this class
        """
        # get the account_key from the model if necessary
        if isinstance(account, db.Model):
            account_key = account.key()
        elif isinstance(account, (str, unicode)):
            account_key = db.Key(account)
        else:
            account_key = account

        c_key_name = cls._get_marketplace_key_name(account_key)

        if from_db:
            return Campaign.get_by_key_name(c_key_name)
        return Campaign(key_name=c_key_name,
                        campaign_type='marketplace',
                        name='MarketPlace',
                        account=account_key)

    @classmethod
    def _get_marketplace_key_name(cls, account_key):
        """
        Returns the key_name based on the account_key
        """
        return 'mkt:%s' % account_key

    @classmethod
    def get_marketplace_campaign(cls, adunit=None):
        """ Returns a marketplace campaign for this adunit,
            Creatives a new campaign if one doesn't exist already
            """
        if adunit is None:
            return None
        camps = cls.get_campaigns(account=adunit.account)
        mkcamp = filter(lambda camp: camp.campaign_type == 'marketplace', camps)
        if mkcamp:
            ag = camp.adgroups
            if adunit.key() not in ag.site_keys:
                ag.site_keys.append(adunit.key())
                ag.put()
            mkcamp.put()
            return mkcamp
        else:
            return cls.add_marketplace_campaign(cls, adunit=adunit)

    @classmethod
    def add_marketplace_campaign(cls, adunit=None):
            """ Adds a marketplace campagin for this adunit
                """
            acct = adunit.account
            camp = Campaign(name = 'Marketplace Campaign',
                                    campaign_type = 'marketplace',
                                    account = acct,
                                    )
            camp.put()
            ag = AdGroup(campaign = camp,
                                 account = acct,
                                 name = 'Marketplace adgroup',
                                 site_keys = [adunit.key()],
                                 )
            ag.put()
            creative = ag.default_creative()
            creative.account = acct
            creative.put()
            return camp

    @classmethod
    def get_campaigns(cls, account=None, adunit=None, deleted=False, limit=MAX_OBJECTS):
        campaigns = Campaign.all()
        if not (deleted == None):
            campaigns = campaigns.filter("deleted =",deleted)
        if account:
            campaigns = campaigns.filter("account =",account)
        return campaigns.fetch(limit)

    @classmethod
    @wraps_first_arg
    def put(cls, campaigns):
        if not isinstance(campaigns, list):
            campaigns = [campaigns]
        
        # Put campaigns so if they're new they have a key    
        put_response = db.put(campaigns)
        
        # They need a key because this QM needs the key
        for camp in campaigns:
            budg_obj = BudgetQueryManager.update_or_create_budget_for_campaign(camp)
            camp.budget_obj = budg_obj

        # Put them again so they save their budget obj
        put_response = db.put(campaigns)


        # Clear cache
        adunits = []
        for campaign in campaigns:
            for adgroup in campaign.adgroups:
                adunits.extend(adgroup.site_keys)

        adunits = AdUnitQueryManager.get(adunits)
        AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

        return put_response


    @classmethod
    def reports_get_campaigns(cls, account=None, publisher=None, advertiser=None, deleted=False, by_priority=False):
        if advertiser:
            # advertiser as list means priority level, return all these camps
            # because we want stuff for those campaigns individually
            if type(advertiser) == list:
                return advertiser
            else:
                return advertiser

        if publisher:
            #publisher is either an app or an adunit, assume it's an adunit first and make it a list
            adunits = [publisher]
            if hasattr(publisher, 'all_adunits'):
                #if it's not an adunit, make it
                adunits = publisher.all_adunits
            adgroups = AdGroup.all().filter('site_keys IN', [a for a in adunits])
            if deleted is not None:
                adgroups = [a for a in adgroups if a.deleted == deleted]
            camps = [adgroup.campaign for adgroup in adgroups]
            if by_priority:
                temp = []
                for p in CAMPAIGN_LEVELS:
                    priority_camps = [c for c in camps if c.campaign_type == p]
                    if len(priority_camps) > 0:
                        temp.append(priority_camps)
                camps = temp
            return camps

        if deleted is not None:
            camps = Campaign.all().filter('deleted =', deleted)
        if account:
            camps = camps.filter('account = ', account)
        #turn a list of campaigns into a list of lists where each list is all
        #campaigns at a given priority level
        if by_priority:
            temp = []
            for p in CAMPAIGN_LEVELS:
                priority_camps = [c for c in camps if c.campaign_type == p]
                if len(priority_camps) > 0:
                    temp.append(priority_camps)
            camps = temp
        return camps



class AdGroupQueryManager(QueryManager):
    Model = AdGroup

    @classmethod
    def get_adgroups(cls, campaign=None, campaigns=None, adunit=None, app=None, account=None, deleted=False, limit=MAX_OBJECTS, archived=False):
        """ archived=True means we only show archived adgroups. """
        adgroups = AdGroup.all()
        if not (deleted == None):
            adgroups = adgroups.filter("deleted =", deleted)
        if account:
            adgroups = adgroups.filter("account =", account)

        if not (archived == None):
            adgroups = adgroups.filter("archived =", archived)

        if campaigns:
            # if the number of campaigns is greater than 30 we must "chunk" the query
            if len(campaigns) > MAX_ALLOWABLE_QUERIES:
                total_adgroups = []
                for sub_campaigns in chunks(campaigns,MAX_ALLOWABLE_QUERIES):
                    adgroups_current = copy.deepcopy(adgroups)
                    total_adgroups += adgroups_current.filter("campaign IN", sub_campaigns).fetch(limit)
                return total_adgroups
            else:
                adgroups = adgroups.filter("campaign IN",campaigns)
        elif campaign:
            adgroups = adgroups.filter("campaign =",campaign)

        if adunit:
            if isinstance(adunit,db.Model):
                adunit_key = adunit.key()
            else:
                adunit_key = adunit
            adgroups = adgroups.filter("site_keys =",adunit_key)

        if app:
            adgroups_dict = {}
            adunits = AdUnitQueryManager.get_adunits(app=app)
            for adunit in adunits:
                adgroups_per_adunit = cls.get_adgroups(adunit=adunit, limit=limit)
                for adgroup in adgroups_per_adunit:
                    adgroups_dict[adgroup.key()] = adgroup
            return adgroups_dict.values()[:limit]

        return adgroups.fetch(limit)

    # TODO: Make all of this DRY
    @classmethod
    def get_network_adgroup(cls, account_key, network_type):
        """
        Returns the only adgroup that can belong to this network
        and account. The magic of key_names allows us to
        avoid getting the object from the db because
        all the information is a function of the adunit itself.

        Note: it is the API consumer's responsiblity to actually
        save this object with the put method of this class
        """

        # Force to string
        account_key = str(account_key)

        # By using a key_name that is one-to-one mapped with the
        # adunit, we can assure that there is only ever one
        # adgroup per adunit
        ag_key_name = cls._get_network_key_name(network_type)

        # if db = True, retrieve from the database vs creating a local copy
        adgroup = AdGroup.get_by_key_name(ag_key_name)
        return adgroup

    @classmethod
    def get_network_adunit_adgroup(cls, adunit_key, account_key, network_type,
            get_from_db=False):
        """
        Returns the only adgroup that can belong to this adunit
        and account. The magic of key_names allows us to
        avoid getting the object from the db because
        all the information is a function of the adunit itself.

        Note: it is the API consumer's responsiblity to actually
        save this object with the put method of this class
        """

        # Force to string
        adunit_key = str(adunit_key)
        account_key = str(account_key)

        # By using a key_name that is one-to-one mapped with the
        # adunit, we can assure that there is only ever one
        # adgroup per adunit
        ag_key_name = cls._get_network_adunit_key_name(adunit_key)

        # if db = True, retrieve from the database vs creating a local copy
        if get_from_db:
            adgroup = AdGroup.get_by_key_name(ag_key_name)
            return adgroup

        adgroup = AdGroup(key_name=ag_key_name, name='Network')
        # set up the rest of the properties
        adgroup.bid_strategy = 'cpm'
        adgroup.account = db.Key(account_key)
        adgroup.network_type = network_type
        adgroup.network_state = NetworkStates.NETWORK_ADUNIT_ADGROUP
        # only targetted at one adunit
        adgroup.site_keys = [db.Key(adunit_key)]

        return adgroup

    @classmethod
    def _get_network_key_name(cls, network_type):
        """
        Returns the key_name based on the adunit_key
        """
        return 'ntwk:%s' % network_type

    @classmethod
    def _get_network_adunit_key_name(cls, adunit_key):
        """
        Returns the key_name based on the adunit_key
        """
        return 'ntwk_au:%s' % adunit_key

    @classmethod
    def get_marketplace_adgroup(cls, adunit_key, account_key, get_from_db=False):
        """
        Returns the only adgroup that can belong to this adunit
        and account. The magic of key_names allows us to
        avoid getting the object from the db because
        all the information is a function of the adunit itself.

        Note: it is the API consumer's responsiblity to actually
        save this object with the put method of this class
        """

        # Force to string
        adunit_key = str(adunit_key)
        account_key = str(account_key)

        # gets the appropriate campaign so that the marketplace
        # adgroup can reference to the correct thing
        # since we only need this to create a reference property
        # and the object has a deterministic key_name
        # we don't need to bother saving.
        campaign = CampaignQueryManager.get_marketplace(account_key)

        # By using a key_name that is one-to-one mapped with the
        # adunit, we can assure that there is only ever one
        # adgroup per adunit
        ag_key_name = cls._get_marketplace_key_name(adunit_key)

        # if db = True, retrieve from the database vs creating a local copy
        if get_from_db:
            adgroup = AdGroup.get_by_key_name(ag_key_name)
            return adgroup

        adgroup = AdGroup(key_name=ag_key_name, name='Marketplace')
        # set up the rest of the properties
        adgroup.bid_strategy = 'cpm'
        adgroup.account = db.Key(account_key)
        adgroup.campaign = campaign
        # only targetted at one adunit
        adgroup.site_keys = [db.Key(adunit_key)]

        return adgroup

    @classmethod
    def _get_marketplace_key_name(cls, adunit_key):
        """
        Returns the key_name based on the adunit_key
        """
        return 'mkt:%s' % adunit_key

    @classmethod
    @wraps_first_arg
    def put(self, adgroups):
        put_response = db.put(adgroups)

        # Clear cache
        adunits = []
        for adgroup in adgroups:
            adunits.extend(adgroup.site_keys)
        adunits = AdUnitQueryManager.get(adunits)
        AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

        return put_response


class CreativeQueryManager(QueryManager):
    Model = Creative

    @classmethod
    def get_creatives(cls,adgroup=None,ad_type=None,ad_types=None,account=None,deleted=False,limit=MAX_OBJECTS):
        creatives = Creative.all()
        if not (deleted == None):
            creatives = creatives.filter("deleted =", deleted)
        if account:
            creatives = creatives.filter("account =", account)
        if adgroup:
            creatives = creatives.filter("ad_group =", adgroup)
        if ad_types:
            creatives = creatives.filter("ad_types IN", ad_types)
        if ad_type:
            creatives = creatives.filter("ad_type =", ad_type)
        return creatives.fetch(limit)

    def put_creatives(self,creatives):
        return db.put(creatives)

    @classmethod
    def reports_get_creatives(cls, account=None, publisher=None, advertiser=None, deleted=False):
        adgroups = []
        #Advertiser will always be a campaign or a list of campaigns
        if advertiser:
            if not isinstance(advertiser, list):
                advertiser = [advertiser]
            for adv in advertiser:
                adgroups += adv.adgroups
        if publisher:
            adunits = [publisher]
            if hasattr(publisher, 'all_adunits'):
                adunits = [au for au in publisher.all_adunits]
            pub_ags = AdGroup.all().filter('site_keys IN', adunits)
            if deleted is not None:
                pub_ags = [a for a in pub_ags if a.deleted == deleted]
            #collect all the adgroups for the publisher and the advertiser
            #make sure to only take the intersection of the sets
            if adgroups:
                final = []
                for pub_ag in pub_ags:
                    for ag in adgroups:
                        if pub_ag.key() == ag.key():
                            final.append(pub_ag)
                adgroups = final
            else:
                adgroups = pub_ags
        if adgroups:
            return reduce(lambda x, y: x+y, [[c for c in ag.creatives] for ag in adgroups])
        crtvs = Creative.all().filter('account =', account)
        if deleted is not None:
            crtvs = crtvs.filter('deleted =', deleted)
        return crtvs



    @classmethod
    @wraps_first_arg
    def put(cls, creatives):
        put_response = db.put(creatives)

        for creative in creatives:
            # update cache
            adunits = AdUnitQueryManager.get(creative.ad_group.site_keys)
            if adunits:
                AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

        return put_response


class TextCreativeQueryManager(CreativeQueryManager):
    Model = TextCreative
class TextAndTileCreativeQueryManager(CreativeQueryManager):
    Model = TextAndTileCreative
class HtmlCreativeQueryManager(CreativeQueryManager):
    Model = HtmlCreative
class ImageCreativeQueryManager(CreativeQueryManager):
    Model = ImageCreative
