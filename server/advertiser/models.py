import logging

from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.db import polymodel
from account.models import Account

from common.constants import MIN_IOS_VERSION, MAX_IOS_VERSION, MIN_ANDROID_VERSION, MAX_ANDROID_VERSION
import datetime
from budget.tzinfo import Pacific


from ad_server.renderers.creative_renderer import BaseCreativeRenderer
from ad_server.renderers.admob import AdMobRenderer
from ad_server.renderers.admob_native import AdMobNativeRenderer
from ad_server.renderers.text_and_tile import TextAndTileRenderer
from ad_server.renderers.adsense import AdSenseRenderer
from ad_server.renderers.image import ImageRenderer
from ad_server.renderers.millennial_native import MillennialNativeRenderer
from ad_server.renderers.millennial import MillennialRenderer
from ad_server.renderers.custom_native import CustomNativeRenderer
from ad_server.renderers.base_html_renderer import BaseHtmlRenderer
from ad_server.renderers.html_data_renderer import HtmlDataRenderer
from ad_server.renderers.brightroll import BrightRollRenderer
from ad_server.renderers.inmobi import InmobiRenderer
from ad_server.renderers.greystripe import GreyStripeRenderer
from ad_server.renderers.appnexus import AppNexusRenderer
from ad_server.renderers.chartboost import ChartBoostRenderer
from ad_server.renderers.ejam import EjamRenderer
from ad_server.renderers.jumptap import JumptapRenderer
from ad_server.renderers.iad import iAdRenderer
from ad_server.renderers.mobfox import MobFoxRenderer


from ad_server.networks.appnexus import AppNexusServerSide
from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.brightroll import BrightRollServerSide
from ad_server.networks.chartboost import ChartBoostServerSide
from ad_server.networks.ejam import EjamServerSide
from ad_server.networks.greystripe import GreyStripeServerSide
from ad_server.networks.inmobi import InMobiServerSide
from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.mobfox import MobFoxServerSide
from ad_server.networks.dummy_server_side import (DummyServerSideSuccess,
                                                  DummyServerSideFailure
                                                 )

from common.utils.helpers import to_uni, to_ascii

# from budget import budget_service
#
# A campaign.    Campaigns have budgetary and time based restrictions.
#
class Campaign(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    campaign_type = db.StringProperty(choices=['gtee', 'gtee_high', 'gtee_low', 'promo', 'network','backfill_promo', 'marketplace', 'backfill_marketplace'])

    # budget per day
    budget = db.FloatProperty()
    full_budget = db.FloatProperty()

    # Determines whether we redistribute if we underdeliver during a day
    budget_type = db.StringProperty(choices=['daily', 'full_campaign'], default="daily")

    # Determines whether we smooth during a day
    budget_strategy = db.StringProperty(choices=['evenly','allatonce'], default="allatonce")

    # start and end dates
    start_date = db.DateProperty()
    end_date = db.DateProperty()

    active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)

    # who owns this
    account = db.ReferenceProperty(Account)
    t = db.DateTimeProperty(auto_now_add=True)

    @property
    def owner_key(self):
        return None

    @property
    def owner_name(self):
        return None

    @property
    def finite(self):
        if (self.start_date and self.end_date):
            return True
        else:
            return False

    def get_owner(self):
        return None

    def set_owner(self, value):
        pass

    def owner(self):
        return property(get_owner, set_owner)

    def delivery(self):
        if self.stats: return self.stats.revenue / self.budget
        else: return 1

    def gtee(self):
        return self.campaign_type in ['gtee', 'gtee_high', 'gtee_low']

    def promo(self):
        return self.campaign_type in ['promo', 'backfill_promo']

    def network(self):
        return self.campaign_type in ['network']

    def marketplace(self):
        return self.campaign_type in ['marketplace', 'backfill_marketplace']

    def is_active_for_date(self, date):
        """ Start and end dates are inclusive """
        if (self.start_date  <= date if self.start_date else True) and (date <= self.end_date if self.end_date else True):
            return True
        else:
            return False


class AdGroup(db.Model):
    campaign = db.ReferenceProperty(Campaign,collection_name="adgroups")
    net_creative = db.ReferenceProperty(collection_name='creative_adgroups')
    name = db.StringProperty()

    # start and end dates
    start_date = db.DateProperty()
    end_date = db.DateProperty()

    created = db.DateTimeProperty(auto_now_add=True)

    # the priority level at which this ad group should be auctioned
    network_type = db.StringProperty(choices=["dummy","adsense", "iAd", "admob","millennial","ejam","chartboost","appnexus","inmobi","mobfox","jumptap","brightroll","greystripe", "custom", "custom_native", "admob_native", "millennial_native"])

    # Note that bid has different meaning depending on the bidding strategy.
    # if CPM: bid = cost per 1000 impressions
    # if CPC: bid = cost per 1 click
    bid = db.FloatProperty(default=0.05, required=False)
    bid_strategy = db.StringProperty(choices=["cpc", "cpm", "cpa"], default="cpc")

    # state of this ad group
    active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)
    archived = db.BooleanProperty(default=False)


    # percent of users to be targetted
    percent_users = db.FloatProperty(default=100.0)
    allocation_percentage = db.FloatProperty(default=100.0)
    allocation_type = db.StringProperty(choices=["users","requests"])

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


    DEVICE_CHOICES = (
        ('any','Any'),
        ('iphone','iPhone'),
        ('ipod','iPod Touch'),
        ('ipad','iPad'),
        ('android','Android'),
        ('blackberry','Blackberry'),
        ('windows7','Windows Phone 7'),
    )
    devices = db.StringListProperty(default=['any'])

    MIN_OS_CHOICES = (
        ('any','Any'),
        ('iphone__2_0','2.0+'),
        ('iphone__2_1','2.1+'),
        ('iphone__3_0','3.0+'),
        ('iphone__3_1','3.1+'),
        ('iphone__3_2','3.2+'),
        ('iphone__4_0','4.0+'),
        ('iphone__4_1','4.1+'),
    )
    min_os = db.StringListProperty(default=['any'])

    # Device Targeting
    device_targeting = db.BooleanProperty(default=False)

    target_iphone = db.BooleanProperty(default=True)
    target_ipod = db.BooleanProperty(default=True)
    target_ipad = db.BooleanProperty(default=True)
    ios_version_min = db.StringProperty(default=MIN_IOS_VERSION)
    ios_version_max = db.StringProperty(default=MAX_IOS_VERSION)

    target_android = db.BooleanProperty(default=True)
    android_version_min = db.StringProperty(default=MIN_ANDROID_VERSION)
    android_version_max = db.StringProperty(default=MAX_ANDROID_VERSION)

    target_other = db.BooleanProperty(default=True) # MobileWeb on blackberry etc.

    USER_TYPES = (
        ('any','Any'),
        ('active_7','7 day active user'),
        ('active_15','15 day active user'),
        ('active_30','30 day active user'),
        ('inactive_7','7 day active user'),
        ('inactive_15','15 day active user'),
        ('inactive_30','30 day inactive user'),
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

    def default_creative(self, custom_html=None, key_name=None):
        # TODO: These should be moved to ad_server/networks or some such
        c = None
        if self.network_type == 'adsense': c = AdSenseCreative(key_name=key_name, name="adsense dummy",ad_type="adsense", format="320x50", format_predicates=["format=*"])
        elif self.network_type == 'iAd': c = iAdCreative(key_name=key_name, name="iAd dummy",ad_type="iAd", format="320x50", format_predicates=["format=320x50"])
        elif self.network_type == 'admob': c = AdMobCreative(key_name=key_name, name="admob dummy",ad_type="admob", format="320x50", format_predicates=["format=320x50"])
        elif self.network_type == 'brightroll': c = BrightRollCreative(key_name=key_name, name="brightroll dummy",ad_type="html_full", format="full",format_predicates=["format=*"])
        elif self.network_type == 'chartboost': c = ChartBoostCreative(key_name=key_name, name="chartboost dummy",ad_type="html",format="320x50",format_predicates=["format=320x50"])
        elif self.network_type == 'ejam': c = EjamCreative(key_name=key_name, name="ejam dummy",ad_type="html",format="320x50",format_predicates=["format=320x50"])
        elif self.network_type == 'jumptap': c = JumptapCreative(key_name=key_name, name="jumptap dummy",ad_type="html", format="320x50",format_predicates=["format=320x50"])
        elif self.network_type == 'millennial': c = MillennialCreative(key_name=key_name, name="millennial dummy",ad_type="html",format="320x50", format_predicates=["format=320x50"]) # TODO: make sure formats are right
        elif self.network_type == 'inmobi': c = InMobiCreative(key_name=key_name, name="inmobi dummy",ad_type="html",format="320x50", format_predicates=["format=320x50"]) # TODO: make sure formats are right
        elif self.network_type == 'greystripe' : c = GreyStripeCreative(key_name=key_name, name="greystripe dummy",ad_type="greystripe", format="320x50", format_predicates=["format=*"]) # TODO: only formats 320x320, 320x48, 300x250
        elif self.network_type == 'appnexus': c = AppNexusCreative(key_name=key_name, name="appnexus dummy",ad_type="html",format="320x50",format_predicates=["format=300x250"])
        elif self.network_type == 'mobfox' : c = MobFoxCreative(key_name=key_name, name="mobfox dummy",ad_type="html",format="320x50",format_predicates=["format=320x50"])
        elif self.network_type == 'custom': c = CustomCreative(key_name=key_name, name='custom', ad_type='html', format='', format_predicates=['format=*'], html_data=custom_html)
        elif self.network_type == 'custom_native': c = CustomNativeCreative(key_name=key_name, name='custom native dummy', ad_type='custom_native', format='320x50', format_predicates=['format=*'], html_data=custom_html)
        elif self.network_type == 'admob_native': c = AdMobNativeCreative(key_name=key_name, name="admob native dummy",ad_type="admob_native",format="320x50",format_predicates=["format=320x50"])
        elif self.network_type == 'millennial_native': c = MillennialNativeCreative(key_name=key_name, name="millennial native dummy",ad_type="millennial_native",format="320x50",format_predicates=["format=320x50"])
        elif self.campaign.campaign_type in ['marketplace', 'backfill_marketplace']: c = MarketplaceCreative(key_name=key_name, name='marketplace dummy', ad_type='html')

        if c: c.ad_group = self
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
        return property(get_owner, set_owner)

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
    def individual_cost(self):
        """ The smallest atomic bid. """
        if self.bid_strategy == 'cpc':
            return self.bid
        elif self.bid_strategy == 'cpm':
            return self.bid/1000

    @property
    def running(self):
        """ Must be active and have proper start and end dates"""
        campaign = self.campaign
        pac_today = datetime.datetime.now(tz=Pacific).date()
        if ((not campaign.start_date or campaign.start_date < pac_today) and
            (not campaign.end_date or campaign.end_date > pac_today)):
            if self.active and campaign.active:
                return True

        return False

    @property
    def created_date(self):
        return self.created.date()


class Creative(polymodel.PolyModel):
    name = db.StringProperty(default='Creative')
    custom_width = db.IntegerProperty()
    custom_height = db.IntegerProperty()
    landscape = db.BooleanProperty(default=False) # TODO: make this more flexible later

    ad_group = db.ReferenceProperty(AdGroup, collection_name="creatives")


    active = db.BooleanProperty(default=True)
    deleted = db.BooleanProperty(default=False)

    # the creative type helps the ad server render the right thing if the creative wins the auction
    ad_type = db.StringProperty(choices=["text", "text_icon", "image", "iAd", "adsense", "admob", "greystripe", "html", "html_full", "clear", "custom_native","admob_native", "millennial_native"], default="image")

    # tracking pixel
    tracking_url = db.StringProperty()

    # destination URLs
    url = db.StringProperty()
    display_url = db.StringProperty()

    # conversion goals
    conv_appid = db.StringProperty()

    # format predicates - the set of formats that this creative can match
    # e.g. format=320x50
    # e.g. format=*
    format_predicates = db.StringListProperty(default=["format=*"])
    format = db.StringProperty(default="320x50") # We should switch to using this field instead of format_predicates: one creative per size

    launchpage = db.StringProperty()

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
    Renderer = BaseCreativeRenderer
    ServerSide = None  # Non-server-bound creatives don't need a serverside

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


class TextCreative(Creative):
    # text ad properties
    headline = db.StringProperty()
    line1 = db.StringProperty()
    line2 = db.StringProperty()

    @property
    def Renderer(self):
        return None

    def __repr__(self):
        return "'%s'" % (self.headline,)

class TextAndTileCreative(Creative):
    line1 = db.StringProperty()
    line2 = db.StringProperty()
    # image = db.BlobProperty()
    image_blob = blobstore.BlobReferenceProperty()
    action_icon = db.StringProperty(choices=["download_arrow4", "access_arrow", "none"], default="download_arrow4")
    color = db.StringProperty(default="000000")
    font_color = db.StringProperty(default="FFFFFF")
    gradient = db.BooleanProperty(default=False)

    @property
    def Renderer(self):
        return TextAndTileRenderer

class HtmlCreative(Creative):
    """ This creative has pure html that has been added by the user.
        This should not be confused with ad_type=html, which means that the
        payload is html as opposed to a native request. """
    html_data = db.TextProperty()

    @property
    def Renderer(self):
        return HtmlDataRenderer


class ImageCreative(Creative):
    # image properties
    # image = db.BlobProperty()
    image_blob = blobstore.BlobReferenceProperty()
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


    @property
    def Renderer(self):
        return ImageRenderer

class MarketplaceCreative(HtmlCreative):
    """ If this is targetted to an adunit, lets the ad_auction know to
        run the marketplace battle. """


class CustomCreative(HtmlCreative):
    # TODO: For now this is redundant with HtmlCreative
    # If we don't want to add any properties to it, remove it
    network_name = "custom"

class CustomNativeCreative(HtmlCreative):
    network_name = "custom_native"
    Renderer = CustomNativeRenderer


    @property
    def multi_format(self):
        return ('728x90', '320x50','300x250', 'full')

class iAdCreative(Creative):
    network_name = "iAd"

    Renderer = iAdRenderer

    @property
    def multi_format(self):
        return ('728x90', '320x50', 'full_tablet')

class AdSenseCreative(Creative):
    network_name = "adsense"

    Renderer = AdSenseRenderer

    @property
    def multi_format(self):
        return ('320x50', '300x250')

class AdMobCreative(Creative):
    network_name = "admob"


    Renderer = AdMobRenderer

class AdMobNativeCreative(AdMobCreative):
    network_name = "admob_native"

    Renderer = AdMobNativeRenderer

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250', 'full' ,)

class MillennialCreative(Creative):

    network_name = "millennial"

    Renderer = MillennialRenderer

    ServerSide = MillennialServerSide

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250',)

class MillennialNativeCreative(MillennialCreative):
    network_name = "millennial_native"

    Renderer = MillennialNativeRenderer

    ServerSide = None

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250', 'full' ,)

class ChartBoostCreative(Creative):

    network_name = "chartboost"

    Renderer = ChartBoostRenderer

    ServerSide = ChartBoostServerSide

    @property
    def multi_format(self):
        return ('320x50', 'full',)

class EjamCreative(Creative):
    network_name = "ejam"

    Renderer = ChartBoostRenderer

    ServerSide = EjamServerSide

class InMobiCreative(Creative):

    network_name = "inmobi"

    Renderer = InmobiRenderer

    ServerSide = InMobiServerSide

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250', '468x60', '120x600',)

class AppNexusCreative(Creative):
    network_name = "appnexus"

    Renderer = AppNexusRenderer

    ServerSide = AppNexusServerSide


class BrightRollCreative(Creative):
    network_name = "brightroll"

    Renderer = BrightRollRenderer

    ServerSide = BrightRollServerSide

    @property
    def multi_format(self):
        return ('full', 'full_tablet')

class JumptapCreative(Creative):
    network_name = "jumptap"

    Renderer = JumptapRenderer

    ServerSide = JumptapServerSide

    @property
    def multi_format(self):
        return ('728x90', '320x50', '300x250')

class GreyStripeCreative(Creative):
    network_name = "greystripe"

    Renderer = GreyStripeRenderer

    ServerSide = GreyStripeServerSide

    @property
    def multi_format(self):
        return ('320x320', '320x50', '300x250',)

class MobFoxCreative(Creative):

    network_name = "mobfox"
    Renderer = MobFoxRenderer

    ServerSide = MobFoxServerSide


class NullCreative(Creative):
    pass

class DummyServerSideFailureCreative(Creative):
    ServerSide = DummyServerSideFailure


class DummyServerSideSuccessCreative(Creative):
    ServerSide = DummyServerSideSuccess
