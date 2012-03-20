""" This is a collection of simplified db.Model objects with ZERO dependencies on
anything that resides within appengine.  These models will function identically
to the ones that live on GAE as far as the adserver is concerned, but they don't
have any of the builtins for db putting and other things that the adserver doesn't
give a shit about """
from datetime import datetime
import logging

MAX_OBJECTS = 200

# TODO(tornado) dereference image blobs to image serving urls for ad_server

def from_basic_type(basic_obj, already_translated = None):
    """ basic_obj is a built-in type that was probably read from JSON or something similar.
        Transform it into full-fledged Python class instances where necessary.
        Apply recursively for lists and dicts.
    """
    # Commenting out the caching because it doesn't help, because the GAE Model objects exist as mutliple copies to begin with.
    #if already_translated is None:
    #    already_translated = {}
    #if id(basic_obj) in already_translated:
    #    logging.warning("Using already-translated (cached) object at address %s: %s" % (id(basic_obj), repr(basic_obj)))
    #    return already_translated[id(basic_obj)]
    #logging.info("Interpreting basic-type %s: %s" % (type(basic_obj), repr(basic_obj)))
    assert basic_obj is None or isinstance(basic_obj, (int, long, float, str, unicode, datetime, dict, list, tuple))
    if isinstance(basic_obj, (list, tuple)):
        # Apply this function recursively on the subobjects.
        to_return = [from_basic_type(x, already_translated) for x in basic_obj]
    elif isinstance(basic_obj, dict):
        # Apply this function recursively on the subobjects.
        basic_obj = dict(basic_obj) # Make a copy.
        for (key, value) in basic_obj.iteritems():
            basic_obj[key] = from_basic_type(value, already_translated)

        if "_TYPE_NAME" in basic_obj:
            # basic_obj represents a class instance.
            # Figure out what class it's meant to represent an instance of.
            type_name = basic_obj["_TYPE_NAME"]
            #logging.info("Looking up class name %s" % type_name)
            simplemodel_class = globals()[type_name]
            assert issubclass(simplemodel_class, SimpleModel)
            del basic_obj["_TYPE_NAME"]
            for (key, value) in basic_obj.iteritems():
                assert not key.startswith("_")
            # Construct a SimpleModel instance using the items of basic_obj as arguments to the constructor.
            to_return = simplemodel_class(**basic_obj)
        else:
            # basic_obj represents a plain dict, that is not meant to represent a class instance.
            to_return = basic_obj
    else:
        # basic_obj represents a basic type (such as int or str).
        to_return = basic_obj
    # Cache this translated object, so that if there are multiple references to a single object, we do not create multiple translated copies.
    # NOTE: This does not handle circular references.
    # Commenting out the caching because it doesn't help, because the GAE Model objects exist as mutliple copies to begin with.
    #already_translated[id(basic_obj)] = to_return
    return to_return

def to_basic_type(obj, already_translated = None):
    """ Transform this Python object into a basic built-in type (such as dict, list, etc) that represents the object.
        Apply recursively for sub-objects. Thus the result will be made entirely of basic built-in types.
        This allows us to serialize the object in JSON or a similar format.
    """
    # Commenting out the caching because it doesn't help, because the GAE Model objects exist as mutliple copies to begin with.
    #if already_translated is None:
    #    already_translated = {}
    #if id(obj) in already_translated:
    #    return already_translated[id(obj)]
    #logging.info("Converting to basic-types: %s %s" % (type(obj), repr(obj)))
    assert obj is None or isinstance(obj, (int, long, float, str, unicode, datetime, dict, list, tuple, SimpleModel))
    if isinstance(obj, (list, tuple)):
        # Apply this function recursively on the subobjects.
        to_return = [to_basic_type(x, already_translated) for x in obj]
    elif isinstance(obj, dict):
        # Apply this function recursively on the subobjects.
        obj = dict(obj) # Make a copy.
        for (key, value) in obj.iteritems():
            obj[key] = to_basic_type(value, already_translated)
        to_return = obj
    elif isinstance(obj, SimpleModel):
        # Transform into a dict that represents this object.
        # The dict contains all the instance variables, plus the name of the class of the object.
        d = {}
        key_transform = {"_key": "key", "_multi_format": "multi_format"}
        for (key, value) in obj.__dict__.iteritems():
            key = key_transform.get(key, key) # Default is no change.
            if key.startswith("_"):
                logging.error("Instance variable with underscore: %s" % key)
            assert not key.startswith("_")
            d[key] = to_basic_type(value, already_translated) # Apply this function recursively on the subobjects.
        d["_TYPE_NAME"] = type(obj).__name__
        to_return = d
    else:
        # obj represents a basic type (such as int or str).
        to_return = obj
    # Cache this translated object, so that if there are multiple references to a single object, we do not create multiple translated copies.
    # - This might matter a lot when we pickle a collection of objects with multiple references to the same object.
    #   Pickle is smart and only serializes the object once, saving space massively (the pickle protocol can even handle circular references).
    #   With JSON however, shared objects will get serialized multiple times separately (and JSON doesn't handle circular references).
    #    - However, it's definitely possible to make it work with JSON. Create a dict (ie JSON 'object') that maps IDs to objects.
    #      Then serialize the data by replacing each object with its id. There is probably a library to do this already.
    # NOTE: This code does not handle circular references.
    # Commenting out the caching because it doesn't help, because the GAE Model objects exist as mutliple copies to begin with.
    #already_translated[id(obj)] = to_return
    return to_return

class SimpleModel(object):
    def to_basic_dict(self):
        return to_basic_type(self)

    def simplify(self):
        return self

    def __eq__(self, other):
        # This is mostly to ease testing.
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def put(self):
        """ This is ONLY for ad_server testing!!
            Puts this SimpleModel into the db stub.
        """
        # Since this file is common code, put the ad_server import here.
        from ad_server.db_stub import get_db_stub
        assert get_db_stub() is not None, "SimpleModel.put() is only for testing. The test db_stub has not been set up."
        get_db_stub().put(self)

    @classmethod
    def get(cls, key):
        """ This is ONLY for ad_server testing!!
            Gets an object of this class from the db stub.
        """
        # Since this file is common code, put the ad_server import here.
        from ad_server.db_stub import get_db_stub
        assert get_db_stub() is not None, "SimpleModel.get() is only for testing. The test db_stub has not been set up."
        obj = get_db_stub().get(key)
        assert isinstance(obj, cls), "Type of object from db_stub did not match expected type."
        return obj

class SimpleAdUnitContext(SimpleModel):
    def __init__(self, adunit, campaigns, adgroups, creatives):
        self.adunit = adunit.simplify()
        self.campaigns = [camp.simplify() for camp in campaigns]
        self.adgroups = [ag.simplify() for ag in adgroups]
        self.creatives = [crtv.simplify() for crtv in creatives]

    def get_creative_by_key(self, creative_key):
        crtv = None
        for c in self.creatives:
            if str(creative_key) == str(c.key()):
                return c

    def get_creatives_for_adgroups(self,adgroups,limit=MAX_OBJECTS):
        """ Get only the creatives for the requested adgroups """
        adgroup_keys = set(adgroup.key() for adgroup in adgroups)
        creatives = [creative for creative in self.creatives
                              if creative.ad_group.key() in adgroup_keys]
        return creatives

    @classmethod
    # TODO(simon): Move this somewhere else
    def key_from_adunit_key(cls, adunit_key):
        """ Since we want a 1-1 mapping from adunits to adunit_contexts, we
        appropriate the key from the adunit, returns a string. """
        return "context:" + str(adunit_key)

    def key(self):
        """ Uses the adunit's key """
        return self.key_from_adunit_key(self.adunit.key())

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'SimpleAdUnitContext: %s' % dict(adunit = self.adunit,
                                                campaigns = self.campaigns,
                                                adgroups = self.adgroups,
                                                creatives = self.creatives)

class SimpleAdUnit(SimpleModel):
    # needs keywords, app_key, format, landscape, resizable, custom heigh, width,
    # adsense_channel_id, ad_type,
    def __init__(self, key=None, app_key=None, format=None, landscape=None,
                 resizable=None, custom_height=None, custom_width=None, keywords=None,
                 adsense_channel_id=None, ad_type=None, account=None, name=None,
                 refresh_interval=None, network_config=None):
        self.account = account.simplify()
        self.name = name
        self._key = key
        self.keywords = keywords
        self.app_key = app_key.simplify()
        self.format = format
        self.landscape = landscape
        self.resizable = resizable
        self.custom_height = custom_height
        self.custom_width = custom_width
        self.adsense_channel_id = adsense_channel_id
        self.ad_type = ad_type
        self.refresh_interval = refresh_interval
        self.network_config = network_config.simplify() if network_config else None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'SimpleAdUnit: %s' % dict(account = self.account,
                                         name = self.name,
                                         key = self._key,
                                         app_key = self.app_key,
                                         )

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

    def key(self):
        return self._key

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

class SimpleCampaign(SimpleModel):
    def __init__(self, key=None, name=None, campaign_type=None, start_datetime=None, end_datetime=None, active=None, deleted=None, account=None):
        self._key = key
        self.name = name
        self.campaign_type = campaign_type
        self.active = active
        self.deleted = deleted
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.account = account.simplify()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "SimpleCampaign: %s" % dict(key = self._key,
                                           name = self.name,
                                           account = self.account,)
    def key(self):
        return self._key

    @property
    def end_date(self):
        if self.end_datetime:
            return self.end_datetime.date()
        else:
            return None

    @property
    def start_date(self):
        if self.start_datetime:
            return self.start_datetime.date()
        else:
            return None

class SimpleAdGroup(SimpleModel):
    def __init__(self,
                 key=None,
                 campaign=None,
                 name=None,
                 bid=None,
                 bid_strategy=None,
                 active=None,
                 deleted=None,
                 minute_frequency_cap=None,
                 hourly_frequency_cap=None,
                 daily_frequency_cap=None,
                 weekly_frequency_cap=None,
                 monthly_frequency_cap=None,
                 lifetime_frequency_cap=None,
                 keywords=None,
                 site_keys=None,
                 account=None,
                 mktplace_price_floor=None,
                 device_targeting=None,
                 target_ipod=None,
                 target_iphone=None,
                 target_ipad=None,
                 ios_version_min=None,
                 ios_version_max=None,
                 target_android=None,
                 android_version_max=None,
                 android_version_min=None,
                 target_other=None,
                 cities=None,
                 geo_predicates=None,
                 allocation_percentage=None
                 ):
        self._key = key
        self.campaign = campaign.simplify()
        self.account = account.simplify()
        self.name = name
        self.bid = bid
        self.bid_strategy = bid_strategy
        self.active = active
        self.deleted = deleted
        self.minute_frequency_cap = minute_frequency_cap
        self.hourly_frequency_cap = hourly_frequency_cap
        self.daily_frequency_cap = daily_frequency_cap
        self.weekly_frequency_cap = weekly_frequency_cap
        self.monthly_frequency_cap = monthly_frequency_cap
        self.lifetime_frequency_cap = lifetime_frequency_cap
        self.keywords = keywords
        self.site_keys = site_keys
        self.mktplace_price_floor = mktplace_price_floor
        self.device_targeting = device_targeting
        self.target_ipod = target_ipod
        self.target_ipad = target_ipad
        self.target_iphone = target_iphone
        self.ios_version_max = ios_version_max
        self.ios_version_min = ios_version_min
        self.target_android = target_android
        self.android_version_min = android_version_min
        self.android_version_max = android_version_max
        self.target_other = target_other
        self.cities = cities
        self.geo_predicates = geo_predicates
        self.allocation_percentage = allocation_percentage

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'SimpleAdGroup: %s' % dict(key = self._key,
                                          campaign = self.campaign,
                                          account = self.account)
    def key(self):
        return self._key

    @property
    def geographic_predicates(self):
        return self.geo_predicates

    @property
    def cpm(self):
        if self.bid_strategy == 'cpm':
            return self.bid
        return None

    @property
    def cpc(self):
        if self.bid_strategy == 'cpc':
            return self.bid
        return None

class SimpleCreative(SimpleModel):
    def __init__(self, key=None, name=None, custom_width=None, custom_height=None, landscape=None, ad_group=None,
                 active=None, deleted=None, ad_type=None, tracking_url=None, url=None, display_url=None, conv_appid=None,
                 format=None, launchpage=None, account=None, multi_format=None, network_name = None):
        self._key = key
        self.name = name
        self.custom_width = custom_width
        self.custom_height = custom_height
        self.landscape = landscape
        self.ad_group = ad_group.simplify()
        self.active = active
        self.deleted = deleted
        self.ad_type = ad_type
        self.tracking_url = tracking_url
        self.url = url
        self.display_url = display_url
        self.conv_appid = conv_appid
        self.format = format
        self.launchpage = launchpage
        self.account = account.simplify()
        self._multi_format = multi_format
        self.network_name = network_name

    def key(self):
        return self._key

    @property
    def multi_format(self):
            return self._multi_format

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

    def _get_adgroup(self):
            return self.ad_group

    def _set_adgroup(self,value):
            self.ad_group = value

    #whoever did this you rule
    adgroup = property(_get_adgroup,_set_adgroup)

class SimpleTextCreative(SimpleCreative):
    def __init__(self, headline=None, line1=None, line2=None, **kwargs):
        self.headline = headline
        self.line1 = line1
        self.line2 = line2
        super(SimpleTextCreative, self).__init__(**kwargs)

class SimpleTextAndTileCreative(SimpleCreative):
    def __init__(self, line1=None, line2=None, image_url=None, action_icon=None,
                 color=None, font_color=None, gradient=None, **kwargs):
        self.line1 = line1
        self.line2 = line2
        self.image_url= image_url
        self.action_icon = action_icon
        self.color = color
        self.font_color = font_color
        self.gradient = gradient
        super(SimpleTextAndTileCreative, self).__init__(**kwargs)

class SimpleHtmlCreative(SimpleCreative):
    def __init__(self, html_data=None, ormma_html=None, **kwargs):
        if html_data is not None:
            html_data = str(html_data)
        if ormma_html is not None:
            ormma_html = str(ormma_html)
        self.html_data = html_data
        self.ormma_html = ormma_html
        super(SimpleHtmlCreative, self).__init__(**kwargs)

class SimpleImageCreative(SimpleCreative):
    def __init__(self, image_url=None, image_height=None, image_width=None, **kwargs):
        self.image_url = image_url
        self.image_height = image_height
        self.image_width = image_width
        super(SimpleImageCreative, self).__init__(**kwargs)

class SimpleNullCreative(SimpleCreative):
    pass

class SimpleDummySuccessCreative(SimpleCreative):
    pass

class SimpleDummyFailureCreative(SimpleCreative):
    pass

class SimpleDummyServerSideSuccessCreative(SimpleDummySuccessCreative):
    pass

class SimpleDummyServerSideFailureCreative(SimpleDummyFailureCreative):
    pass

class SimpleApp(SimpleModel):
    # both cats, global_id, package, type, need config, experimental_fraction
    # admob things, adsense things,
    def __init__(self, key=None, account=None, global_id=None, adsense_app_name=None, adsense_app_id=None,
                 admob_bgcolor=None, admob_textcolor=None, app_type=None, package=None, url=None,
                 network_config=None, primary_category=None, secondary_category=None, name=None,
                 experimental_fraction=.001):
        self._key = key
        self.account = account.simplify()
        self.global_id = global_id
        self.name = name
        self.adsense_app_name = adsense_app_name
        self.adsense_app_id = adsense_app_id
        self.admob_textcolor = admob_textcolor
        self.admob_bgcolor = admob_bgcolor
        self.app_type = app_type
        self.package = package
        self.url = url
        self.network_config = network_config.simplify() if network_config else None
        self.primary_category = primary_category
        self.secondary_category = secondary_category
        self.experimental_fraction = experimental_fraction

    def key(self):
        return self._key

class SimpleAccount(SimpleModel):
    def __init__(self, key=None, company=None, domain=None, network_config=None,
                 adsense_company_name=None, adsense_test_mode=None):
        self._key = key
        self.company = company
        self.domain = domain
        self.network_config = network_config.simplify() if network_config else None
        self.adsense_company_name = adsense_company_name
        self.adsense_test_mode = adsense_test_mode

    def key(self):
        return self._key

class SimpleNetworkConfig(SimpleModel):
    def __init__(self, key=None, admob_pub_id=None, adsense_pub_id=None,
                 brightroll_pub_id=None, chartboost_pub_id=None, ejam_pub_id=None,
                 greystripe_pub_id=None, inmobi_pub_id=None, jumptap_pub_id=None,
                 millennial_pub_id=None, mobfox_pub_id=None, rev_share=None,
                 price_floor=None, blocklist=None, blind=None, blocked_cat=None, blocked_attrs=None,
                 category_blocklist=None, attribute_blocklist=None):
        self._key = key
        self.admob_pub_id = admob_pub_id
        self.adsense_pub_id = adsense_pub_id
        self.brightroll_pub_id = brightroll_pub_id
        self.chartboost_pub_id = chartboost_pub_id
        self.ejam_pub_id = ejam_pub_id
        self.greystripe_pub_id = greystripe_pub_id
        self.inmobi_pub_id = inmobi_pub_id
        self.jumptap_pub_id = jumptap_pub_id
        self.millennial_pub_id = millennial_pub_id
        self.mobfox_pub_id = mobfox_pub_id
        self.rev_share = rev_share
        self.price_floor = price_floor
        self.blocklist = blocklist
        self.blind = blind
        self.category_blocklist = category_blocklist
        self.attribute_blocklist = attribute_blocklist

    def key(self):
        return self._key



# For testing on the tornado ad_server, we want to stop using the GAE models.
# So we're going to use the SimpleModels instead.
# But for clarity, and to make it easier to change later,
# we're going to refer to them by a different name in the tests.
TestModel                          = SimpleModel
TestAdUnitContext                  = SimpleAdUnitContext
TestAdUnit                         = SimpleAdUnit
TestCampaign                       = SimpleCampaign
TestAdGroup                        = SimpleAdGroup
TestCreative                       = SimpleCreative
TestTextCreative                   = SimpleTextCreative
TestTextAndTileCreative            = SimpleTextAndTileCreative
TestHtmlCreative                   = SimpleHtmlCreative
TestImageCreative                  = SimpleImageCreative
TestNullCreative                   = SimpleNullCreative
TestDummyFailureCreative           = SimpleDummyFailureCreative
TestDummySuccessCreative           = SimpleDummySuccessCreative
TestDummyServerSideSuccessCreative = SimpleDummyServerSideSuccessCreative
TestDummyServerSideFailureCreative = SimpleDummyServerSideFailureCreative
TestApp                            = SimpleApp
TestAccount                        = SimpleAccount
TestNetworkConfig                  = SimpleNetworkConfig


