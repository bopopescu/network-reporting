import logging


from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.db import polymodel
from google.appengine.api import images
from account.models import Account

from common.constants import (MIN_IOS_VERSION,
                              MAX_IOS_VERSION,
                              MIN_ANDROID_VERSION,
                              MAX_ANDROID_VERSION,
                              IOS_VERSION_CHOICES,
                              ISO_COUNTRY_LOOKUP_TABLE,
                              ANDROID_VERSION_CHOICES,
                              NETWORKS)
import datetime
import time


from common.utils.helpers import to_uni

from budget.models import Budget
from simple_models import (SimpleAdGroup,
                           SimpleCampaign,
                           SimpleCreative,
                           SimpleHtmlCreative,
                           SimpleImageCreative,
                           SimpleTextAndTileCreative,
                           SimpleNullCreative,
                           SimpleDummyFailureCreative,
                           SimpleDummySuccessCreative,
                           )
from budget.memcache_budget import total_spent

class NetworkStates:
    """
    Network states
    """
    # STANDARD_CAMPAIGN is not a new network campaign
    STANDARD_CAMPAIGN = 0
    DEFAULT_NETWORK_CAMPAIGN = 1
    CUSTOM_NETWORK_CAMPAIGN = 2


class Campaign(db.Model):
    """
    Campaigns are essentially containers for adgroups.
    They have a name, advertiser, and description, some basic state,
    and an account. All other information should be added to AdGroup.
    """
    name = db.StringProperty(verbose_name='Name',
                             default='Order Name',
                             required=True)
    advertiser = db.StringProperty(verbose_name='Advertiser:',
                                   default='Advertiser Name',
                                   required=True)
    description = db.StringProperty(verbose_name='Description:',
                                    multiline=True)

    # current state
    active = db.BooleanProperty(default=True)
    archived = db.BooleanProperty(default=False)
    deleted = db.BooleanProperty(default=False)

    # who owns this?
    account = db.ReferenceProperty(Account)

    # date of creation
    created = db.DateTimeProperty(auto_now_add=True)

    # is this a campaign for direct sold (an order), marketplace, or networks?
    campaign_type = db.StringProperty(choices=['order',
                                               'marketplace',
                                               'network'])

    # If the campaign is a new network campaign then the network field is
    # set otherwise it's left blank
    #
    # NETWORKS are used to instantiate the network field in campaigns
    #
    # Compared to an AdGroup (network_type):
    #       admob = admob_native
    #       millennial = millennial_native
    #       iad = iAd
    network_type = db.StringProperty(choices=NETWORKS.keys(), default='')
    network_state = db.IntegerProperty(default=NetworkStates.STANDARD_CAMPAIGN)
    # needed so old stats can be mapped to the new campaign on migration
    # since we can't keep the same campaign key for optimization purposes
    old_campaign = db.SelfReferenceProperty()
    transition_date = db.DateProperty()

    @property
    def is_order(self):
        return self.campaign_type == 'order'

    @property
    def is_marketplace(self):
        return self.campaign_type == 'marketplace'

    @property
    def is_network(self):
        return self.campaign_type == 'network'

    def simplify(self):
        return SimpleCampaign(key = str(self.key()),
                              name = self.name,
                              advertiser = self.advertiser,
                              active = self.active,
                              account = self.account)

    def __repr__(self):
        return "Campaign: %s, owned by %s, for %s" % (self.name,
                                                      self.account,
                                                      self.advertiser)
    @property
    def owner_key(self):
        return None

    @property
    def owner_name(self):
        return None

    def get_owner(self):
        return None

    def set_owner(self, value):
        pass

    def owner(self):
        return property(self.get_owner, self.set_owner)

    def toJSON(self):
        return {
            'name': self.name,
            'advertiser': self.advertiser,
            'description': self.description,
            'active': self.active,
            'deleted': self.deleted,
            'key': str(self.key())
        }

    @property
    def status_icon_url(self):
        if self.deleted:
            return "/images/deleted.gif"
        if self.active:
            return "/images/active.gif"
        if self.archived:
            return "/images/archived.gif"

        return "/images/paused.gif"


Order = Campaign


class AdGroup(db.Model):
    campaign = db.ReferenceProperty(Campaign, collection_name="adgroups")
    # net_creative is not set for new network campaigns due to circular
    # reference redundancy, use the creatives collection instead
    net_creative = db.ReferenceProperty(collection_name='creative_adgroups')
    name = db.StringProperty(verbose_name='Name',
                             default='Line Item Name',
                             required=True)

    created = db.DateTimeProperty(auto_now_add=True)

    # the priority level at which this ad group should be auctioned
    network_type = db.StringProperty(choices=["dummy",  # ?
                                              "adsense",
                                              "iAd",
                                              "admob",  # deprecated, but may still be used by some accounts
                                              "millennial",  # deprecated, but may still be used by some accounts
                                              "ejam",
                                              "chartboost",  # deprecated
                                              "appnexus",  # deprecated
                                              "inmobi",
                                              "mobfox",
                                              "jumptap",
                                              "brightroll",
                                              "greystripe",  # deprecated, but may still be used by some accounts
                                              "custom",
                                              "custom_native",
                                              "admob_native",
                                              "millennial_native"])

    # Note that bid has different meaning depending on the bidding strategy.
    # if CPC: bid = cost per 1 click
    # if CPM: bid = cost per 1000 impressions
    # if CPA: bid = cost per 1000 conversions
    bid = db.FloatProperty(default=0.05, required=False)
    bid_strategy = db.StringProperty(choices=["cpc", "cpm", "cpa"], default="cpm")

    #############################
    # moved from campaign class #
    #############################

    # budget per day
    daily_budget = db.FloatProperty()
    full_budget = db.FloatProperty()
    # Determines whether we redistribute if we underdeliver during a day
    budget_type = db.StringProperty(choices=['daily', 'full_campaign'],
                                    default="daily")
    # Determines whether we smooth during a day
    budget_strategy = db.StringProperty(choices=['evenly', 'allatonce'],
                                        default="allatonce")

    budget_obj = db.ReferenceProperty(Budget, collection_name='adgroup')

    # New start and end date properties
    start_datetime = db.DateTimeProperty()
    end_datetime = db.DateTimeProperty()

    adgroup_type = db.StringProperty(choices=['gtee',
                                              'gtee_high',
                                              'gtee_low',
                                              'promo',
                                              'network',
                                              'backfill_promo',
                                              'marketplace'])

    ##################################
    # /end moved from campaign class #
    ##################################

    # state of this ad group
    active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)
    archived = db.BooleanProperty(default=False)

    # percent of users to be targetted
    percent_users = db.FloatProperty(default=100.0)
    allocation_percentage = db.FloatProperty(verbose_name='Allocation',
                                             default=100.0)
    allocation_type = db.StringProperty(choices=["users", "requests"])

    # frequency caps
    minute_frequency_cap = db.IntegerProperty(default=0)
    hourly_frequency_cap = db.IntegerProperty(default=0)
    daily_frequency_cap = db.IntegerProperty(default=0)
    weekly_frequency_cap = db.IntegerProperty(default=0)
    monthly_frequency_cap = db.IntegerProperty(default=0)
    lifetime_frequency_cap = db.IntegerProperty(default=0)

    # all keyword and category bids are tracked here
    # categories use the category:games convention
    # if any of the input keywords match the n-grams here then we
    # trigger a match
    keywords = db.StringListProperty()

    # all placements that are considered for this ad group
    # this is a list of keys corresponding to Site objects
    site_keys = db.ListProperty(db.Key)

    account = db.ReferenceProperty(Account)
    t = db.DateTimeProperty(auto_now_add=True)

    # marketplace price floor
    mktplace_price_floor = db.FloatProperty(default=0.25, required=False)

    DEVICE_CHOICES = (
        ('any', 'Any'),
        ('iphone', 'iPhone'),
        ('ipod', 'iPod Touch'),
        ('ipad', 'iPad'),
        ('android', 'Android'),
        ('blackberry', 'Blackberry'),
        ('windows7', 'Windows Phone 7'),
    )
    devices = db.StringListProperty(default=['any'])

    MIN_OS_CHOICES = (
        ('any', 'Any'),
        ('iphone__2_0', '2.0+'),
        ('iphone__2_1', '2.1+'),
        ('iphone__3_0', '3.0+'),
        ('iphone__3_1', '3.1+'),
        ('iphone__3_2', '3.2+'),
        ('iphone__4_0', '4.0+'),
        ('iphone__4_1', '4.1+'),
    )
    min_os = db.StringListProperty(default=['any'])

    # Device Targeting
    device_targeting = db.BooleanProperty(default=False)

    target_iphone = db.BooleanProperty(verbose_name='iPhone', default=True)
    target_ipod = db.BooleanProperty(verbose_name='iPod', default=True)
    target_ipad = db.BooleanProperty(verbose_name='iPad', default=True)
    ios_version_min = db.StringProperty(verbose_name='Min:',
                                        default=MIN_IOS_VERSION)
    ios_version_max = db.StringProperty(verbose_name='Max:',
                                        default=MAX_IOS_VERSION)

    target_android = db.BooleanProperty(verbose_name='Android', default=True)
    android_version_min = db.StringProperty(verbose_name='Min:',
                                            default=MIN_ANDROID_VERSION)
    android_version_max = db.StringProperty(verbose_name='Max:',
                                            default=MAX_ANDROID_VERSION)

    target_other = db.BooleanProperty(verbose_name='Other:',default=True)  # MobileWeb on blackberry etc.

    optimizable = db.BooleanProperty(default=False)
    default_cpm = db.FloatProperty()

    USER_TYPES = (
        ('any', 'Any'),
        ('active_7', '7 day active user'),
        ('active_15', '15 day active user'),
        ('active_30', '30 day active user'),
        ('inactive_7', '7 day active user'),
        ('inactive_15', '15 day active user'),
        ('inactive_30', '30 day inactive user'),
    )

    active_user = db.StringListProperty(default=['any'])
    active_app = db.StringListProperty(default=['any'])
    cities = db.StringListProperty(default=[])

    country = db.StringProperty()
    region = db.StringProperty()
    state = db.StringProperty()
    city = db.StringProperty()

    # Geographic preferences are expressed as string tuples that can match
    # the city, region or country that is resolved via reverse geocode at
    # request time.    If the list is blank, any value will match. If the list
    # is not empty, the value must match one of the elements of the list.
    #
    # Valid predicates are:
    # city_name=X,region_name=X,country_name=X
    # region_name=X,country_name=X
    # country_name=X
    # zipcode=X
    #
    # Each incoming request will be matched against all of these combinations
    geo_predicates = db.StringListProperty(default=["country_name=*"])

    # negative user targeting
    included_apps = db.ListProperty(db.Key)
    excluded_apps = db.ListProperty(db.Key)

    @property
    def included_apps_global_ids(self):
        global_ids = []
        for app_key in self.included_apps or []:
            app = db.get(app_key)
            if app.global_id:
                global_ids.append(app.global_id)
        return global_ids

    @property
    def excluded_apps_global_ids(self):
        global_ids = []
        for app_key in self.excluded_apps or []:
            app = db.get(app_key)
            if app.global_id:
                global_ids.append(app.global_id)
        return global_ids

    @property
    def has_daily_budget(self):
        return self.daily_budget and self.budget_type == 'daily'

    @property
    def has_full_budget(self):
        return self.full_budget and self.budget_type == 'full_campaign'

    @property
    def calculated_cpm(self):
        """
        Calculate the ecpm for a cpc campaign.
        """
        if self.cpc and self.stats.impression_count:
            return (float(self.stats.click_count) * float(self.bid) * 1000.0 /
                    float(self.stats.impression_count))
        return self.bid

    @property
    def line_item_priority(self):
        ranks = {
            'gtee_high': 1,
            'gtee': 2,
            'gtee_low': 3,
            'promo': 4,
            'backfill_promo': 5
        }
        return ranks[self.adgroup_type]

    @property
    def status(self):
        if self.deleted:
            return "deleted"
        elif self.archived:
            return "archived"
        elif self.active:
            now = datetime.datetime.now()
            if (self.start_datetime <= now if self.start_datetime else True) and \
               (now <= self.end_datetime if self.end_datetime else True):
                return "running"
            elif self.end_datetime <= now:
                return "completed"
            else:
                return "scheduled"
        else:
            return "paused"
        return "running"

    @property
    def pace(self):
        try:
            return self.budget_obj.last_slice_log.pace
        except:
            return None

    @property
    def pace_indicator(self):
        pace = self.pace
        if pace > .8:
            return 'pace-success'
        elif pace >= .4:
            return 'pace-warning'
        else:
            return 'pace-failure'

    @property
    def progress(self):
        """ Get the % of the budget that has been delivered """
        budget = self.budget_obj
        if not budget:
            return None
        if budget.static_slice_budget and not budget.finite:
            spent_today = budget.spent_today
            if spent_today:
                return budget.daily_budget / (spent_today * 1.0)
            else:
                return 0.0

        total_budget = budget.total_budget
        if total_budget:
            # includes the memcache spending
            return total_spent(budget) / (total_budget * 1.0)
        else:
            logging.warning("OMG no total budget...? %s" % budget)
            return None

    @property
    def adgroup_type_display(self):
        kinds = {
            'gtee_high': "Guaranteed (High)",
            'gtee': "Guaranteed",
            'gtee_low': "Guaranteed (Low)",
            'promo': "Promotional",
            "backfill_promo": "Backfill Promotional",
            "network": "Network",
            "marketplace": "Marketplace"
        }

        if self.adgroup_type:
            return kinds[self.adgroup_type]
        return ''

    def simplify(self):
        if self.start_date and not self.start_datetime:
            strt = self.start_date
            start_datetime = datetime.datetime(strt.year, strt.month, strt.day)
        else:
            start_datetime = self.start_datetime
        if self.end_date and not self.end_datetime:
            end = self.end_date
            end_datetime = datetime.datetime(end.year, end.month, end.day)
        else:
            end_datetime = self.end_datetime

        return SimpleAdGroup(key = str(self.key()),
                             campaign = self.campaign,
                             account = self.account,
                             name = self.name,
                             bid = self.bid,
                             bid_strategy = self.bid_strategy,
                             active = self.active,
                             deleted = self.deleted,
                             minute_frequency_cap= self.minute_frequency_cap,
                             hourly_frequency_cap= self.hourly_frequency_cap,
                             daily_frequency_cap= self.daily_frequency_cap,
                             weekly_frequency_cap= self.weekly_frequency_cap,
                             monthly_frequency_cap= self.monthly_frequency_cap,
                             lifetime_frequency_cap= self.lifetime_frequency_cap,
                             keywords = self.keywords,
                             site_keys = [str(key) for key in self.site_keys],
                             mktplace_price_floor = self.mktplace_price_floor,
                             device_targeting = self.device_targeting,
                             target_iphone = self.target_iphone,
                             target_ipad = self.target_ipad,
                             target_ipod = self.target_ipod,
                             ios_version_max = self.ios_version_max,
                             ios_version_min = self.ios_version_min,
                             target_android = self.target_android,
                             android_version_max = self.android_version_max,
                             android_version_min = self.android_version_min,
                             target_other = self.target_other,
                             cities = self.cities,
                             geo_predicates = self.geo_predicates,
                             allocation_percentage = self.allocation_percentage,
                             optimizable = self.optimizable,
                             default_cpm = self.default_cpm,
                             network_type = self.network_type,
                             # Added as part of orders feature
                             adgroup_type = self.adgroup_type,
                             start_datetime=start_datetime,
                             end_datetime=end_datetime,
                             full_budget=self.full_budget,
                             daily_budget=self.budget,
                             budget_type=self.budget_type,
                             included_apps = self.included_apps_global_ids,
                             excluded_apps = self.excluded_apps_global_ids,
                             )

    def default_creative(self, custom_html=None, key_name=None):
        # TODO: These should be moved to ad_server/networks or some such
        c = None
        if self.network_type == 'adsense':
            c = AdSenseCreative(key_name=key_name,
                                name="adsense dummy",
                                ad_type="adsense",
                                format="320x50",
                                format_predicates=["format=*"])
        elif self.network_type == 'iAd':
            c = iAdCreative(key_name=key_name,
                            name="iAd dummy",
                            ad_type="iAd",
                            format="320x50",
                            format_predicates=["format=320x50"])
        elif self.network_type == 'admob':
            c = AdMobCreative(key_name=key_name,
                              name="admob dummy",
                              ad_type="admob",
                              format="320x50",
                              format_predicates=["format=320x50"])
        elif self.network_type == 'brightroll':
            c = BrightRollCreative(key_name=key_name,
                                   name="brightroll dummy",
                                   ad_type="html_full",
                                   format="full",
                                   format_predicates=["format=*"])
        elif self.network_type == 'chartboost':
            c = ChartBoostCreative(key_name=key_name,
                                   name="chartboost dummy",
                                   ad_type="html",
                                   format="320x50",
                                   format_predicates=["format=320x50"])
        elif self.network_type == 'ejam':
            c = EjamCreative(key_name=key_name,
                             name="ejam dummy",
                             ad_type="html",
                             format="320x50",
                             format_predicates=["format=320x50"])
        elif self.network_type == 'jumptap':
            c = JumptapCreative(key_name=key_name,
                                name="jumptap dummy",
                                ad_type="html",
                                format="320x50",
                                format_predicates=["format=320x50"])
        elif self.network_type == 'millennial':
            c = MillennialCreative(key_name=key_name,
                                   name="millennial dummy",
                                   ad_type="html",
                                   format="320x50",
                                   format_predicates=["format=320x50"]) # TODO: make sure formats are right
        elif self.network_type == 'inmobi':
            c = InMobiCreative(key_name=key_name,
                               name="inmobi dummy",
                               ad_type="html",
                               format="320x50",
                               format_predicates=["format=320x50"]) # TODO: make sure formats are right
        elif self.network_type == 'greystripe' :
            c = GreyStripeCreative(key_name=key_name,
                                   name="greystripe dummy",
                                   ad_type="greystripe",
                                   format="320x50",
                                   format_predicates=["format=*"]) # TODO: only formats 320x320, 320x48, 300x250
        elif self.network_type == 'appnexus':
            c = AppNexusCreative(key_name=key_name,
                                 name="appnexus dummy",
                                 ad_type="html",
                                 format="320x50",
                                 format_predicates=["format=300x250"])
        elif self.network_type == 'mobfox' :
            c = MobFoxCreative(key_name=key_name,
                               name="mobfox dummy",
                               ad_type="html",
                               format="320x50",
                               format_predicates=["format=320x50"])
        elif self.network_type == 'custom':
            c = CustomCreative(key_name=key_name,
                               name='custom',
                               ad_type='html',
                               format='',
                               format_predicates=['format=*'],
                               html_data=custom_html)
        elif self.network_type == 'custom_native':
            c = CustomNativeCreative(key_name=key_name,
                                     name='custom native dummy',
                                     ad_type='custom_native',
                                     format='320x50',
                                     format_predicates=['format=*'],
                                     html_data=custom_html)
        elif self.network_type == 'admob_native':
            c = AdMobNativeCreative(key_name=key_name,
                                    name="admob native dummy",
                                    ad_type="admob_native",
                                    format="320x50",
                                    format_predicates=["format=320x50"])
        elif self.network_type == 'millennial_native':
            c = MillennialNativeCreative(key_name=key_name,
                                         name="millennial native dummy",
                                         ad_type="millennial_native",
                                         format="320x50",
                                         format_predicates=["format=320x50"])
        elif self.adgroup_type in ['marketplace', 'backfill_marketplace']:
            c = MarketplaceCreative(key_name=key_name,
                                    name='marketplace dummy',
                                    ad_type='html')

        if c:
            c.ad_group = self
        return c

    def __repr__(self):
        return u"AdGroup:%s" % to_uni(self.name)

    @property
    def uses_default_device_targeting(self):

        if self.target_iphone == False or \
        self.target_ipod == False or \
        self.target_ipad == False or \
        self.ios_version_min != MIN_IOS_VERSION or \
        self.ios_version_max != MAX_IOS_VERSION or \
        self.target_android == False or \
        self.android_version_min != MIN_ANDROID_VERSION or \
        self.android_version_max != MAX_ANDROID_VERSION or \
        self.target_other == False:
            return False
        else:
            return True

    @property
    def geographic_predicates(self):
        return self.geo_predicates

    def get_owner(self):
        return self.campaign

    def set_owner(self, value):
        self.campaign = value

    def owner(self, value):
        return property(self.get_owner, self.set_owner)

    @property
    def owner_key(self):
        return self._campaign

    @property
    def owner_name(self):
        return 'campaign'

    @property
    def cpc(self):
        if self.bid_strategy == 'cpc':
            return self.bid
        return None

    @property
    def cpm(self):
        if self.bid_strategy == 'cpm':
            return self.bid
        return None

    @property
    def budget_goal(self):
        try:
            if self.bid_strategy == 'cpm':
                if self.budget_type == 'daily':
                    return int((self.daily_budget / self.bid) * 1000)
                else:
                    return int((self.full_budget / self.bid) * 1000)
            else:
                if self.budget_type == 'daily':
                    return int(self.daily_budget)
                else:
                    return int(self.full_budget)
        except TypeError:
            # We'll get a NoneType exception if no budget is set
            return None

    @property
    def budget_goal_display(self):
        goal = self.budget_goal

        if goal:
            if self.bid_strategy == 'cpm':
                if self.budget_type == 'daily':
                    return str(goal) + ' Impressions Daily'
                else:
                    return str(goal) + ' Impressions Total'
            else:
                if self.budget_type == 'daily':
                    return str(goal) + ' USD Daily'
                else:
                    return str(goal) + ' USD Total'
        else:
            return "Unlimited budget"

    @property
    def individual_cost(self):
        """ The smallest atomic bid. """
        if self.bid_strategy == 'cpc':
            return self.bid
        elif self.bid_strategy == 'cpm':
            return self.bid / 1000

    @property
    def running(self):
        """ Must be active and have proper start and end dates"""
        campaign = self.campaign
        pac_today = datetime.datetime.now().date()
        if ((not campaign.start_date or campaign.start_date < pac_today) and
            (not campaign.end_date or campaign.end_date > pac_today)):
            if self.active and campaign.active:
                return True

        return False


    @property
    def created_date(self):
        return self.created.date()


    @property
    def frequency_cap_display(self):

        display = []

        if self.minute_frequency_cap:
            display.append(str(self.minute_frequency_cap) + "/minute")
        if self.hourly_frequency_cap:
            display.append(str(self.hourly_frequency_cap) + "/hour")
        if self.daily_frequency_cap:
            display.append(str(self.daily_frequency_cap) + "/day")
        if self.weekly_frequency_cap:
            display.append(str(self.weekly_frequency_cap) + "/week")
        if self.monthly_frequency_cap:
            display.append(str(self.monthly_frequency_cap) + "/month")
        if self.lifetime_frequency_cap:
            display.append(str(self.lifetime_frequency_cap) + " total")

        if not display:
            return "No frequency caps"
        else:
            return ", ".join(display)

    @property
    def country_targeting_display(self):

        display = []
        for country in self.geo_predicates:
            country_id = country.strip("country_name=")
            if country_id.find("*") == -1:
                country_name = ISO_COUNTRY_LOOKUP_TABLE[country_id]
                display.append(country_name)

        if not display:
            return "All countries"
        else:
            return ", ".join(sorted(display))

    @property
    def device_targeting_display(self):

        if self.device_targeting and not self.uses_default_device_targeting:

            display = []

            # iOS Targeting
            ios_display = []
            if self.target_iphone:
                ios_display.append("iPhone")
            if self.target_ipad:
                ios_display.append("iPad")
            if self.target_ipod:
                ios_display.append("iPod")

            if ios_display:
                ios_display_all = ", ".join(ios_display) + \
                                  " (iOS version " + self.ios_version_min + \
                                  " to " + self.ios_version_max + ")"
                display.append(ios_display_all)

            # Android Targeting
            if self.target_android:
                android_display_all = "Android Devices (version " + \
                                      self.android_version_min + " to " + \
                                      self.android_version_max + ")"
                display.append(android_display_all)

            if self.target_other:
                display.append("Other Devices")

            if display:
                return display

        return ["All devices"]

    def toJSON(self):
        d = {
            'key': str(self.key()),
            'campaign_key': str(self.campaign.key()),
            'name': self.name,
            'created': self.created,
            'network_type': self.network_type,
            'bid': self.bid,
            'bid_strategy': self.bid_strategy,
            'budget_type': self.budget_type,
            'budget_strategy': self.budget_strategy,
            'adgroup_type': self.adgroup_type,
            'start_datetime': self.start_datetime,
            'end_datetime': self.end_datetime,
            'device_targeting': self.device_targeting_display,
            'country_targeting': self.country_targeting_display,
            'frequency_caps': self.frequency_cap_display,
            'allocation': self.allocation_percentage,
        }
        return d

    #############################
    # moved from campaign class #
    #############################

    @property
    def finite(self):
        if (self.start_datetime and self.end_datetime):
            return True
        else:
            return False

    def delivery(self):
        if self.stats:
            return self.stats.revenue / self.budget
        else:
            return 1

    def gtee(self):
        return self.adgroup_type in ['gtee', 'gtee_high', 'gtee_low']

    def promo(self):
        return self.adgroup_type in ['promo', 'backfill_promo']

    def network(self):
        return self.adgroup_type in ['network']

    def marketplace(self):
        return self.adgroup_type in ['marketplace']

    def is_active_for_date(self, date):
        """ Start and end dates are inclusive """
        if (self.start_date <= date if self.start_date else True) and \
           (date <= self.end_date if self.end_date else True):
            return True
        else:
            return False

    ##################################
    # /end moved from campaign class #
    ##################################

    @property
    def status_icon_url(self):
        if self.deleted:
            return "/images/deleted.gif"
        if self.active and self.campaign.active:
            return "/images/active.gif"
        if self.archived or self.campaign.archived:
            return "/images/archived.gif"

        return "/images/paused.gif"

LineItem = AdGroup


class Creative(polymodel.PolyModel):
    name = db.StringProperty(verbose_name='Creative Name',
                             default='Creative',
                             required=True)
    custom_width = db.IntegerProperty()
    custom_height = db.IntegerProperty()
    landscape = db.BooleanProperty(default=False) # TODO: make this more flexible later

    ad_group = db.ReferenceProperty(AdGroup, collection_name="creatives")

    active = db.BooleanProperty(default=True)
    was_active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)

    # the creative type helps the ad server render the right thing if the creative wins the auction
    ad_type = db.StringProperty(choices=["text_icon", "image", "html",
                                         "iAd", "adsense", "admob",
                                         "greystripe", "html_full", "clear",
                                         "custom_native", "admob_native",
                                         "millennial_native"],
                                default="image")

    # tracking pixel
    tracking_url = db.StringProperty(verbose_name='Impression Tracking URL')

    # destination URLs
    url = db.StringProperty(verbose_name='Click URL')
    display_url = db.StringProperty()

    # conversion goals
    conv_appid = db.StringProperty(verbose_name='Conversion Tracking ID')

    # format predicates - the set of formats that this creative can match
    # e.g. format=320x50
    # e.g. format=*
    format_predicates = db.StringListProperty(default=["format=*"])
    # We should switch to using this field instead of
    # format_predicates: one creative per size
    format = db.StringProperty(default="320x50")

    launchpage = db.StringProperty(verbose_name='Intercept URL')

    # time of creation
    account = db.ReferenceProperty(Account)
    t = db.DateTimeProperty(auto_now_add=True)

    # DEPRECATED: metrics such as e_cpm and CTR only make sense within the context of matching a creative with an adunit
    # Use /ad_server/optimizer/optimizer.py instead to calculate these metrics.
    #
    # def e_cpm(self):
    #     if self.ad_group.bid_strategy == 'cpc':
    #         return float(self.p_ctr() * self.ad_group.bid * 1000)
    #     elif self.ad_group.bid_strategy == 'cpm':
    #         return float(self.ad_group.bid)

    network_name = None
    SIMPLE = SimpleCreative

    @property
    def intercept_url(self):
        """ A URL prefix for which navigation should be intercepted and
            forwarded to a full-screen browser.

            For some ad networks, a click event actually results in navigation
            via "window.location = [TARGET_URL]". Since this kind of navigation is
            not limited exclusively to clicks, only a subset of all observed
            [TARGET_URL]s should be intercepted. This header is used as part of
            prefix-matching to distinguish true click events.
        """
        return self.launchpage

    # Set up the basic Renderers and ServerSides for the creative
    #Renderer = BaseCreativeRenderer
    #ServerSide = None  # Non-server-bound creatives don't need a serverside

    @property
    def multi_format(self):
            return None

    def _get_adgroup(self):
            return self.ad_group

    def _set_adgroup(self,value):
            self.ad_group = value

    #whoever did this you rule
    adgroup = property(_get_adgroup,_set_adgroup)

    def get_owner(self):
        return self.ad_group

    def set_owner(self, value):
        self.ad_group = value

    def _get_width(self):
        if self.custom_width:
            return self.custom_width
        if hasattr(self,'_width'):
            return self._width
        width = 0
        if self.format:
            parts = self.format.split('x')
            if len(parts) == 2:
                width = parts[0]
        return width
    def _set_width(self,value):
        self._width = value
    width = property(_get_width,_set_width)

    def _get_height(self):
        if self.custom_height:
            return self.custom_height
        if hasattr(self,'_height'):
            return self._height

        height = 0
        if self.format:
            parts = self.format.split('x')
            if len(parts) == 2:
                height = parts[1]
        return height

    def _set_height(self, value):
        self._height = value

    height = property(_get_height,_set_height)


    def owner(self):
        return property(get_owner, set_owner)

    @property
    def owner_key(self):
        return self._ad_group

    @property
    def owner_name(self):
        return 'ad_group'

    def __repr__(self):
        return "Creative{ad_type=%s, key_name=%s}" % (self.ad_type, self.key().id_or_name())


    def build_simplify_dict(self):
        return dict(key = str(self.key()),
                    name = self.name,
                    custom_width = self.custom_width,
                    custom_height = self.custom_height,
                    landscape = self.landscape,
                    ad_group = self.ad_group,
                    active = self.active,
                    ad_type = self.ad_type,
                    tracking_url = self.tracking_url,
                    url = self.url,
                    display_url = self.display_url,
                    conv_appid = self.conv_appid,
                    format = self.format,
                    launchpage = self.launchpage,
                    account = self.account,
                    multi_format = self.multi_format,
                    network_name = self.network_name)

    def simplify(self):
        simplify_dict = self.build_simplify_dict()
        return self.SIMPLE(**simplify_dict)


class TextAndTileCreative(Creative):
    SIMPLE = SimpleTextAndTileCreative

    line1 = db.StringProperty(verbose_name='Line 1')
    line2 = db.StringProperty(verbose_name='Line 2')
    # image = db.BlobProperty()
    image_blob = blobstore.BlobReferenceProperty()
    image_serve_url = db.StringProperty()
    action_icon = db.StringProperty(choices=["download_arrow4", "access_arrow", "none"], default="download_arrow4")
    color = db.StringProperty(verbose_name='Background Color',
                              default="000000")
    font_color = db.StringProperty(verbose_name='Font Color',
                                   default="FFFFFF")
    gradient = db.BooleanProperty(verbose_name='Gradient',
                                  default=True)

    def build_simplify_dict(self):
        try:
            img_url = images.get_serving_url(self.image_blob)
        except:
            img_url = "http://curezone.com/upload/Members/new03/white.jpg"
        spec_dict = dict(line1 = self.line1,
                         line2 = self.line2,
                         image_url = img_url,
                         action_icon = self.action_icon,
                         color = self.color,
                         font_color = self.font_color,
                         gradient = self.gradient)

        spec_dict.update(super(TextAndTileCreative, self).build_simplify_dict())
        return spec_dict


class HtmlCreative(Creative):
    """ This creative has pure html that has been added by the user.
        This should not be confused with ad_type=html, which means that the
        payload is html as opposed to a native request. """

    SIMPLE = SimpleHtmlCreative
    html_data = db.TextProperty()
    ormma_html = db.BooleanProperty(verbose_name='MRAID Ad',
                                    default=False)

    def build_simplify_dict(self):
        spec_dict = dict(html_data = self.html_data,
                         ormma_html = self.ormma_html)

        spec_dict.update(super(HtmlCreative, self).build_simplify_dict())
        return spec_dict


    #@property
    #def Renderer(self):
    #    return HtmlDataRenderer


class ImageCreative(Creative):
    SIMPLE = SimpleImageCreative
    # image properties
    # image = db.BlobProperty()
    image_blob = blobstore.BlobReferenceProperty()
    image_serve_url = db.StringProperty()
    image_width = db.IntegerProperty(default=320)
    image_height = db.IntegerProperty(default=480)

    @classmethod
    def get_format_predicates_for_image(c, img):
        IMAGE_PREDICATES = {"300x250": "format=300x250",
            "320x50": "format=320x50",
            "300x50": "format=320x50",
            "728x90": "format=728x90",
            "468x60": "format=468x60"}
        fp = IMAGE_PREDICATES.get("%dx%d" % (img.width, img.height))
        return [fp] if fp else None

    def build_simplify_dict(self):
        spec_dict = dict(image_url = self.image_serve_url,
                         image_width = self.image_width,
                         image_height = self.image_height,
                         )

        spec_dict.update(super(ImageCreative, self).build_simplify_dict())
        return spec_dict

    #@property
    #def Renderer(self):
    #    return ImageRenderer


class MarketplaceCreative(HtmlCreative):
    """ If this is targetted to an adunit, lets the ad_auction know to
        run the marketplace battle. """

    @property
    def multi_format(self):
        return ('728x90', '320x50','300x250', '160x600', 'full', 'full_tablet')


class CustomCreative(HtmlCreative):
    # TODO: For now this is redundant with HtmlCreative
    # If we don't want to add any properties to it, remove it
    network_name = "custom"


class CustomNativeCreative(HtmlCreative):
    network_name = "custom_native"
    #Renderer = CustomNativeRenderer

    @property
    def multi_format(self):
        return ('728x90', '320x50','300x250', 'full')


class iAdCreative(Creative):
    network_name = "iAd"

    #Renderer = iAdRenderer

    @property
    def multi_format(self):
        return ('728x90', '320x50', 'full_tablet')


class AdSenseCreative(Creative):
    network_name = "adsense"

    #Renderer = AdSenseRenderer

    @property
    def multi_format(self):
        return ('320x50', '300x250')


class AdMobCreative(Creative):
    network_name = "admob"


    #Renderer = AdMobRenderer


class AdMobNativeCreative(AdMobCreative):
    network_name = "admob_native"

    #Renderer = AdMobNativeRenderer

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250', 'full' ,)


class MillennialCreative(Creative):

    network_name = "millennial"

    #Renderer = MillennialRenderer

    #ServerSide = MillennialServerSide

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250',)


class MillennialNativeCreative(MillennialCreative):
    network_name = "millennial_native"

    #Renderer = MillennialNativeRenderer

    #ServerSide = None

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250', 'full' , 'full_tablet')


class ChartBoostCreative(Creative):

    network_name = "chartboost"

    #Renderer = ChartBoostRenderer

    #ServerSide = ChartBoostServerSide

    @property
    def multi_format(self):
        return ('320x50', 'full',)


class EjamCreative(Creative):
    network_name = "ejam"

    #Renderer = ChartBoostRenderer

    #ServerSide = EjamServerSide
    @property
    def multi_format(self):
        return ('320x50', 'full',)


class InMobiCreative(Creative):

    network_name = "inmobi"

    #Renderer = InmobiRenderer

    #ServerSide = InMobiServerSide

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250', '468x60', '120x600',)


class AppNexusCreative(Creative):
    network_name = "appnexus"

    #Renderer = AppNexusRenderer

    #ServerSide = AppNexusServerSide


class BrightRollCreative(Creative):
    network_name = "brightroll"

    #Renderer = BrightRollRenderer

    #ServerSide = BrightRollServerSide

    @property
    def multi_format(self):
        return ('full', 'full_tablet')


class JumptapCreative(Creative):
    network_name = "jumptap"

    #Renderer = JumptapRenderer

    #ServerSide = JumptapServerSide

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250')


class GreyStripeCreative(Creative):
    network_name = "greystripe"

    #Renderer = GreyStripeRenderer

    #ServerSide = GreyStripeServerSide

    @property
    def multi_format(self):
        return ('320x320', '320x50', '300x250',)


class MobFoxCreative(Creative):
    network_name = "mobfox"
    #Renderer = MobFoxRenderer

    #ServerSide = MobFoxServerSide

    @property
    def multi_format(self):
        return ('728x90', '320x50')


class NullCreative(Creative):
    SIMPLE = SimpleNullCreative


class DummyServerSideFailureCreative(Creative):
    SIMPLE = SimpleDummyFailureCreative
    #ServerSide = DummyServerSideFailure


class DummyServerSideSuccessCreative(Creative):
    SIMPLE = SimpleDummySuccessCreative
    #ServerSide = DummyServerSideSuccess
