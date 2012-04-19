"""
asdfasdf
"""
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.api import users
from django.conf import settings
from account.models import Account, NetworkConfig
from advertiser.models import Creative
from simple_models import SimpleApp, SimpleAdUnit

import datetime
import time
import logging
import re

#
# A mobile app, which can have multiple Sites on which ads can be displayed
#
class App(db.Model):
    APPLE_DEVICES = ('iphone', 'ipad')
    IAD_URL = 'http://itunes.apple.com.*'

    CATEGORY_CHOICES = (
        u'not_selected',
        u'books',
        u'business',
        u'education',
        u'entertainment',
        u'finance',
        u'games',
        u'healthcare_and_fitness',
        u'lifestyle',
        u'medical',
        u'music',
        u'navigation',
        u'news',
        u'photography',
        u'productivity',
        u'reference',
        u'social_networking',
        u'sports',
        u'travel',
        u'utilities',
        u'weather',
    )

    account = db.ReferenceProperty(Account)

    name = db.StringProperty(required=True)
    global_id = db.StringProperty() # used to store appstore or marketplace id
    adsense_app_name = db.StringProperty()
    adsense_app_id = db.StringProperty()
    admob_bgcolor = db.StringProperty()
    admob_textcolor = db.StringProperty()
    app_type = db.StringProperty(required=True,
                                 default='iphone',
                                 choices=['iphone', 'android', 'ipad', 'mweb'])
    description = db.TextProperty()
    url = db.StringProperty()
    package = db.StringProperty()
    # For MPX
    categories = db.StringListProperty()

    icon_blob = blobstore.BlobReferenceProperty()

    # Ad network overrides
    jumptap_app_id = db.StringProperty()
    millennial_app_id = db.StringProperty()

    deleted = db.BooleanProperty(default=False)

    t = db.DateTimeProperty(auto_now_add=True)

    exchange_creative = db.ReferenceProperty(Creative)

    experimental_fraction = db.FloatProperty(default=0.0)

    network_config = db.ReferenceProperty(NetworkConfig, collection_name="apps")

    primary_category = db.StringProperty(choices=CATEGORY_CHOICES)
    secondary_category = db.StringProperty(choices=CATEGORY_CHOICES)

    use_proxy_bids = db.BooleanProperty(default=True)

    def simplify(self):
        return SimpleApp(key = str(self.key()),
                         account = self.account,
                         name = self.name,
                         global_id = self.global_id,
                         adsense_app_name = self.adsense_app_name,
                         adsense_app_id = self.adsense_app_id,
                         admob_textcolor = self.admob_textcolor,
                         admob_bgcolor = self.admob_bgcolor,
                         app_type = self.app_type,
                         package = self.package,
                         url = self.url,
                         experimental_fraction = self.experimental_fraction,
                         network_config = self.network_config,
                         primary_category = self.primary_category,
                         secondary_category = self.secondary_category)

    def app_type_text(self):
        types = {
            'iphone': 'iOS',
            'android': 'Android',
            'ipad': 'iPad',
            'mweb': 'Mobile Web'
        }
        return types[self.app_type]

    @property
    def icon_url(self):
        from common.utils import helpers
        if not self.icon_blob:
            return "/placeholders/image.gif"
        try:
            url = helpers.get_url_for_blob(self.icon_blob)
            # hack to get images to appear on localhost
            if settings.DEBUG:
                url = url.replace('https', 'http')
            return url
        except Exception:
            return "/placeholders/image.gif"

    @property
    def identifier(self):
        return (self.name.replace(' ', '_') + '-' + self.app_type).lower()

    @property
    def full_name(self):
        return self.name + " (" + self.app_type_text() + ")"

    @property
    def key_(self):
        return str(self.key())

    def get_owner(self):
        return None

    def set_owner(self, value):
        pass

    def owner(self):
        return property(get_owner, set_owner)

    @property
    def owner_key(self):
        return None

    @property
    def owner_name(self):
        return None

    @property
    def iad_pub_id(self):
        if self.app_type in self.APPLE_DEVICES and getattr(self, 'url', None) and \
                re.match(self.IAD_URL, self.url):
            ids = re.findall('/id[0-9]*\?', self.url)
            if ids:
                pub_id = ids[0][len('/id'):-1]
                return pub_id

    def toJSON(self):
        d = to_dict(self, ignore = ['icon', 'account', 'network_config'])
        d.update(icon_url=self.icon_url)
        return d

    def external_key(self):
        return db.Key.from_path(self.key().kind(), self.key().id_or_name(), _app='mopub-inc')

        
class Site(db.Model):
    DEVICE_FORMAT_CHOICES = (
           u'phone',
           u'tablet',
       )

    FORMAT_CHOICES = (
          u'full',
          u'full_tablet',
          u'full_landscape',
          u'full_tablet_landscape',
          u'728x90',
          u'300x250',
          u'160x600',
          u'320x50',
          u'custom',
      )
    # TODO: Why is this "app_key" and not "app"? Answer: app is a reserved word
    # in app engine. This would definitely make more sense to rename app
    # though since it obviously isn't a key.
    app_key = db.ReferenceProperty(App, collection_name="all_adunits")
    account = db.ReferenceProperty(Account)

    # TODO: figure out how to expose this
    adsense_channel_id = db.StringProperty()

    name = db.StringProperty(required=True, default='Banner Ad')
    url = db.StringProperty()
    description = db.TextProperty()
    custom_width = db.IntegerProperty()
    custom_height = db.IntegerProperty()

    device_format = db.StringProperty(default='phone', choices=DEVICE_FORMAT_CHOICES)
    #TODO: we should use this w/o explicity using height, width
    format = db.StringProperty(choices=FORMAT_CHOICES)
    resizable = db.BooleanProperty(default=False)
    landscape = db.BooleanProperty(default=False)

    deleted = db.BooleanProperty(default=False)

    # what kind of ad is preferred here
    ad_type = db.StringProperty(choices=['text', 'image'],
                                default='image',
                                required=False)

    # Ad network overrides
    jumptap_site_id = db.StringProperty()
    millennial_site_id = db.StringProperty()

    # additional keywords that are passed to the auction
    keywords = db.TextProperty() # TODO: make sure this doesn't break shit
    # keywords = db.StringListProperty()

    refresh_interval = db.IntegerProperty(default=0)
    # XXX: this is a string in case we don't want enumeration later
    animation_type = db.StringProperty(default='0')

    # color scheme
    color_border = db.StringProperty(required=True, default='336699')
    color_bg = db.StringProperty(required=True, default='FFFFFF')
    color_link = db.StringProperty(required=True, default='0000FF')
    color_text = db.StringProperty(required=True, default='000000')
    color_url = db.StringProperty(required=True, default='008000')

    # creation time
    t = db.DateTimeProperty(auto_now_add=True)

    network_config = db.ReferenceProperty(NetworkConfig, collection_name="adunits")

    def simplify(self):
        return SimpleAdUnit(key = str(self.key()),
                            name = self.name,
                            account = self.account,
                            app_key = self.app_key,
                            keywords = self.keywords,
                            format = self.format,
                            landscape = self.landscape,
                            resizable = self.resizable,
                            custom_height = self.custom_height,
                            custom_width = self.custom_width,
                            adsense_channel_id = self.adsense_channel_id,
                            ad_type = self.ad_type,
                            refresh_interval = self.refresh_interval,
                            network_config = self.network_config,
                            )


    def toJSON(self):
        d = to_dict(self, ignore = ['account', 'network_config', 'app_key'])
        d['app_key'] = str(self.app_key.key())
        return d

    def is_fullscreen(self):
        return 'full' in self.format

    def is_tablet(self):
        return 'tablet' in self.format

    def get_height(self):
        if self.format == 'custom' and self.custom_height:
            return self.custom_height
        dimensions = self.format.split('x')
        if len(dimensions) > 1:
            return int(dimensions[1])
        else:
            return 0

    def get_width(self):
        if self.format == 'custom' and self.custom_width:
            return self.custom_width
        dimensions = self.format.split('x')
        if len(dimensions) > 1:
            return int(dimensions[0])
        else:
            return 0

    # Now we can access app_key using app
    def _get_app(self):
        return self.app_key
    def _set_app(self, value):
        self.app_key = value
    app = property(_get_app, _set_app)

    @classmethod
    def site_by_id(c, id):
        if id.startswith('ca'):
            account = Account.gql('where adsense_pub_id = :1', id).get()
            s = Site.gql('where account = :1', account).get()
        else:
            s = Site.get(id)
        return s

    def get_owner(self):
        return self.app_key

    def set_owner(self, value):
        self.app_key = value

    def owner(self):
        return property(get_owner, set_owner)

    @property
    def owner_key(self):
        return self._app_key

    @property
    def owner_name(self):
        return "app_key"

    def get_code_format(self):
        code_formats = {
            '728x90': "MOPUB_LEADERBOARD_SIZE",
            '300x250': "MOPUB_MEDIUM_RECT_SIZE",
            '160x600': "MOPUB_WIDE_SKYSCRAPER_SIZE",
            '320x50': "MOPUB_BANNER_SIZE",
            'custom': "CGSizeMake(" + str(self.get_width()) + ", " + str(self.get_height()) +")",
        }
        return code_formats.get(self.format, None)

    def get_pub_id(self, pub_id_attr):
        """ Look up the pub string in all levels """

        # If not found, return None
        adunit_level_id = getattr(self.network_config, pub_id_attr, None)
        if adunit_level_id:
            return adunit_level_id

        app_level_id = getattr(self.app.network_config, pub_id_attr, None)
        if app_level_id:
            return app_level_id

        account_level_id = getattr(self.account.network_config, pub_id_attr, None)
        if account_level_id:
            return account_level_id

    def external_key(self):
        return db.Key.from_path(self.key().kind(), self.key().id_or_name(), _app='mopub-inc')            

###############
# rename Site #
###############

AdUnit = Site


# Serialization

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

def to_dict(model, ignore = None):
    if ignore == None:
        ignore = []

    output = {}
    output.update(id=str(model.key()))
    properties = model.properties().iteritems()

    for key, prop in properties:
        value = getattr(model, key)
        if key in ignore:
            output[key] = '_ignored'
        elif value is None or isinstance(value, SIMPLE_TYPES):
            output[key] = value
        elif isinstance(value, datetime.date):
            # Convert date/datetime to ms-since-epoch ("new Date()").
            ms = time.mktime(value.utctimetuple()) * 1000
            ms += getattr(value, 'microseconds', 0) / 1000
            output[key] = int(ms)
        elif isinstance(value, db.GeoPt):
            output[key] = {'lat': value.lat, 'lon': value.lon}
        elif isinstance(value, db.Model):
            output[key] = to_dict(value)
        else:
            output[key] = 'Could not encode'
            #raise ValueError('cannot encode ' + repr(prop))

    return output
