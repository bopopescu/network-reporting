from __future__ import with_statement
import os
import sys
import datetime
import logging
import simplejson


#### IF THESE TESTS ARE FAILING, SET THIS TO TRUE, RUN AGAIN, THEN SET
#### BACK TO FALSE AND TRY AGAIN.  IF THEY STILL FAIL THEN
#### SOMETHING IS BROKEN
RESET_EXAMPLE = False

sys.path.append(os.environ['PWD'])
import unittest

import common.utils.test.setup as s
s = s #quiet PyLint

from account.models import Account
from publisher.models import App, AdUnit
from advertiser.models import Campaign, AdGroup

from publisher.query_managers import AdUnitContextQueryManager

from google.appengine.ext import testbed
from google.appengine.ext.db import Key

from nose.tools import eq_, ok_

from account.models import NetworkConfig

from advertiser.models import (HtmlCreative,
                               ImageCreative,
                               TextAndTileCreative,
                               )

from ad_server.auction.client_context import ClientContext
from ad_server.renderers.creative_renderer import (BaseCreativeRenderer,
                                                   CLK_URL,
                                                   CLK_URL_ESC,
                                                   CACHEBUSTER,
                                                   ADGROUP_ID,
                                                   CREATIVE_ID,
                                                   CLK_THRU,
                                                   CLK_THRU_ESC,
                                                   CLK_THRU_2ESC,
                                                   UDID,
                                                   )
from ad_server.renderers.header_context import HeaderContext
from ad_server.renderers.get_renderer import get_renderer_for_creative

################# KEY CONSTANSTS (makes tests work) #############
CREATIVE_KEY = 'agltb3B1Yi1pbmNyFgsSCENyZWF0aXZlIghrZXlfbmFtZQw'
APP_KEY = ''
ADUNIT_KEY = 'agltb3B1Yi1pbmNyEgsSBFNpdGUiCGtleV9uYW1lDA'

def deep_dict_eq(dict1, dict2, keys_that_have_json_vals):
    """ Compare two dictionaries to determine equality. Properly loads and compares JSON values, 
    assuming that their corresponding keys are passed in as a list."""
    
    # Given a key, return whether the two dictionaries have the same value
    # Works properly for json values, if they are passed in to deep_dict_eq()
    def values_equal_for_key(key):
        if key in keys_that_have_json_vals:
            return simplejson.loads(dict1[key]) == simplejson.loads(dict2[key])
        else:
            return dict1[key] == dict2[key]
    
    # Dictionaries are only equal if they have the same keys
    if set(dict1.keys()) != set(dict2.keys()):
        return False
    
    # Short-circuit and return False if the values differ for any key
    return all([values_equal_for_key(key) for key in dict1.keys()])

class RenderingTestBase(object):
    """ This does not inherit from TestCase because we use Nose's
        generator function with it.
    """
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        # Set up default models
        self.account = Account()
        self.account.put()

        self.campaign = Campaign(name="Test Campaign")
        self.campaign.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()


        self.network_config = NetworkConfig(account=self.account, admob_pub_id='myadmobsiteid')
        self.network_config.put()

        self.adunit = AdUnit(account=self.account,
                             app_key=self.app,
                             name="Test AdUnit",
                             format="320x50",
                             network_config=self.network_config)
        self.adunit.put()


        self.adgroup = AdGroup(account=self.account,
                               campaign=self.campaign,
                               site_keys=[self.adunit.key()],
                               bid_strategy="cpc",
                               bid=100.0)
        self.adgroup.put()


        self.host = "app.mopub.com"
        self.url = """http://app.mopub.com/m/ad?test_url"""
        self.request_id = 'my_request_id'

        self.keywords = ["awesome","stuff"]

        self.version_number = 6 # Not sure what this is used for

        self.track_url = "test_track_url"

        self.on_fail_exclude_adgroups = ["test_on_fail_adgroup1",
                                         "test_on_fail_adgroup2"]

        self.ios_client_context = ClientContext(user_agent='iphone adfsdf')
        self.android_client_context = ClientContext(user_agent='android adfsdf')

        # self.request = fake_request(self.adunit.key())
        adunit_id = str(self.adunit.key())

        self.adunit_context = AdUnitContextQueryManager.\
                                    cache_get_or_insert(adunit_id)

        self.dt = datetime.datetime(1955, 5, 5, 5, 5)
        self.udid = 'myudid'

    def tearDown(self):
        self.testbed.deactivate()

    def render_320x50_creative(self, network_type):
        """ For now just test the renderer. Next test headers too.
            Uses a default value for html_data. """

        print network_type
        self.adunit = AdUnit(key_name='key_name',
                             account=self.account,
                             app_key=self.app,
                             name="Test AdUnit",
                             format="320x50",
                             network_config=self.network_config)
        self.adunit.put()
        self.adgroup.network_type = network_type
        self.adgroup.put()

        self.creative = self.adgroup.default_creative(key_name='key_name')
        # TODO: Use the actual serverside methods to build this
        self.creative.html_data = "fake data"

        self.creative.put()

        self._compare_rendering_with_examples(network_type, suffix="")



    def render_full_creative(self, network_type):
        """ Tests both the rendering of the creative payload
            Uses a default value for html_data. """

        print network_type
        self.adunit = AdUnit(account=self.account,
                     app_key=self.app,
                     name="Test AdUnit",
                     format="full",
                     network_config=self.network_config)
        self.adunit.put()
        self.adgroup.network_type = network_type
        self.adgroup.put()

        self.creative = self.adgroup.default_creative(key_name='key_name')
        # TODO: Use the actual serverside methods to build this
        self.creative.html_data = "fake data"

        self.creative.put()

        self._compare_rendering_with_examples(network_type, suffix="_full")

    def _compare_rendering_with_examples(self, name, suffix="",
                                               reset_example=RESET_EXAMPLE):
        """ For now just test the renderer. Next test headers too.
            Uses a default value for html_data. """

        self.creative.Renderer = get_renderer_for_creative(self.creative)
        creative_renderer = self.creative.Renderer(creative=self.creative,
                       adunit=self.adunit,
                       udid=self.udid,
                       client_context=self.ios_client_context,
                       now=self.dt,
                       request_host=self.host,
                       request_url=self.url,
                       request_id=self.request_id,
                       version=self.version_number,
                       on_fail_exclude_adgroups=self.on_fail_exclude_adgroups,
                       keywords=['hi','bye'],
                       random_val='0932jfios',
                       testing = True)

        rendered_creative, header_context = creative_renderer.render()


        if reset_example:
            with open("ad_server/renderers/tests/example_renderings/"\
                        "%s%s.rendering" % (name, suffix), 'w') as f:
                f.write(rendered_creative)

        with open("ad_server/renderers/tests/example_renderings/"\
                    "%s%s.rendering" % (name, suffix), 'r') as f:
            example_creative = f.read()

        eq_(rendered_creative, example_creative)

        if reset_example:
            with open("ad_server/renderers/tests/example_renderings/"\
                        "%s%s.headers" % (name, suffix), 'w') as f:
                # We serialize the headers
                header_json = header_context.to_json()
                f.write(header_json)

        with open("ad_server/renderers/tests/example_renderings/"\
                    "%s%s.headers" % (name, suffix), 'r') as f:
            example_headers_string = f.read()
            example_headers = HeaderContext.\
                                from_json(unicode(example_headers_string))

        print "running file name: %s" % name
        print header_context
        print example_headers
        # Modified to use deep_dict_eq (as to appropriately load X-Nativeparams)
        ok_(deep_dict_eq(header_context._dict, example_headers._dict, ['X-Nativeparams']))



class HeaderContextTests(unittest.TestCase):

    def mptest_basic_header_test(self):
        """
        Very basic test of HeaderContext. Just ensures that passed in parameter
        values get translated correctly into the actual header names while
        excluding 'None' values
        """
        header_context = HeaderContext(refresh_time=1,
                                       intercept_links="link!",
                                       click_through='11',
                                       imp_tracker="imp_tracker.com",
                                       orientation=1,
                                       launch_page='aaa',
                                       scrollable='scrollable_val'
                                       )
        header_dict = {'X-Interceptlinks': 'link!',
                       'X-Clickthrough': '11',
                       'X-Scrollable': 'scrollable_val',
                       'X-Orientation': '1',
                       'X-Launchpage': 'aaa',
                       'X-Imptracker': 'imp_tracker.com',
                       'X-Refreshtime': '1'}
        eq_(header_context._dict, header_dict)


class RenderingTests(RenderingTestBase, unittest.TestCase):
    """ Inherits that setUp and tearDown methods from RenderingTestBase. """


    def mptest_base_creative(self):
        """ Tests the base creative renderer """

        self.creative = HtmlCreative(key_name="key_name",
                                     name="image dummy",
                                     ad_type="html",
                                     html_data="test html data",
                                     format="320x50",
                                     format_predicates=["format=320x50"],
                                     tracking_url="http://www.google.com/",
                                     ad_group=self.adgroup,
                                     launchpage="http://www.google.com2/")

        renderer = BaseCreativeRenderer(
                     creative=self.creative,
                     adunit=self.adunit,
                     udid=self.udid,
                     now=self.dt,
                     request_host=self.host,
                     request_url=self.url,
                     request_id=self.request_id,
                     version=self.version_number,
                     client_context=self.android_client_context,
                     on_fail_exclude_adgroups=self.on_fail_exclude_adgroups,
                     keywords=['hi','bye'],
                     random_val='0932jfios')
        try:
            renderer._setup_headers()
        except NotImplementedError:
            try:
                renderer._setup_content()
            except NotImplementedError:
                return

        ok_(False, "Exceptions not raised")

    def mptest_html_adtype(self):
        """ Make a one-off test for html creatives. """

        adgroup = AdGroup(account=self.account,
                          campaign=self.campaign,
                          site_keys=[self.adunit.key()],
                          bid_strategy="cpm",
                          bid=100.0)
        adgroup.put()

        self.creative = HtmlCreative(key_name="key_name",
                                     name="image dummy",
                                     ad_type="html",
                                     html_data="test html data",
                                     format="320x50",
                                     format_predicates=["format=320x50"],
                                     tracking_url="http://www.google.com/",
                                     ad_group=adgroup,
                                     launchpage="http://www.google.com2/")

        self.creative.image_width = 320
        self.creative.image_height = 50
        self.creative.put()

        _on_fail_exclude_adgroups = [e for e in self.on_fail_exclude_adgroups]
        self.on_fail_exclude_adgroups = []


        # For this test we want to makes sure that the templates
        # are correct for fullscreen tablets
        # (i.e. the meta tag)
        old_format = self.adunit.format
        self.adunit.format = '320x50'

        self._compare_rendering_with_examples("html_adtype", suffix="")

        self.adunit.format = old_format

        self.on_fail_exclude_adgroups = _on_fail_exclude_adgroups

    def mptest_html_full_adtype(self):
        """ Make a one-off test for html creatives. """

        adgroup = AdGroup(account=self.account,
                          campaign=self.campaign,
                          site_keys=[self.adunit.key()],
                          bid_strategy="cpm",
                          bid=100.0)
        adgroup.put()

        self.creative = HtmlCreative(key_name="key_name",
                                     name="image dummy",
                                     ad_type="html",
                                     html_data="test html data",
                                     format="320x50",
                                     format_predicates=["format=320x50"],
                                     tracking_url="http://www.google.com/",
                                     ad_group=adgroup,
                                     launchpage="http://www.google.com2/")

        self.creative.image_width = 320
        self.creative.image_height = 50
        self.creative.put()

        _on_fail_exclude_adgroups = [e for e in self.on_fail_exclude_adgroups]
        self.on_fail_exclude_adgroups = []


        # For this test we want to makes sure that the templates
        # are correct for fullscreen tablets
        # (i.e. the meta tag)
        old_format = self.adunit.format
        self.adunit.format = 'full_tablet'

        self._compare_rendering_with_examples("html_full", suffix="")

        self.adunit.format = old_format

        self.on_fail_exclude_adgroups = _on_fail_exclude_adgroups


    def mptest_mraid_html_adtype(self):
        """ Make a one-off test for mraid creatives. """

        adgroup = AdGroup(account=self.account,
                          campaign=self.campaign,
                          site_keys=[self.adunit.key()],
                          bid_strategy="cpm",
                          bid=100.0)
        adgroup.put()

        self.creative = HtmlCreative(key_name="key_name",
                                     name="image dummy",
                                     ad_type="html",
                                     html_data="<html>test mraid data</html>",
                                     format="320x50",
                                     format_predicates=["format=320x50"],
                                     tracking_url="http://www.google.com/pingme",
                                     ad_group=adgroup,
                                     ormma_html=True,
                                     launchpage="http://www.google.com2/")

        self.creative.image_width = 320
        self.creative.image_height = 50
        self.creative.put()

        _on_fail_exclude_adgroups = [e for e in self.on_fail_exclude_adgroups]
        self.on_fail_exclude_adgroups = []

        # For this test we want to makes sure that the templates
        # are correct for fullscreen tablets
        # (i.e. the meta tag)
        old_format = self.adunit.format

        self._compare_rendering_with_examples("mraid_adtype", suffix="")

        self.adunit.format = old_format

        self.on_fail_exclude_adgroups = _on_fail_exclude_adgroups

    def mptest_mraid_html_full_adtype(self):
        """ Make a one-off test for mraid creatives. """

        adgroup = AdGroup(account=self.account,
                          campaign=self.campaign,
                          site_keys=[self.adunit.key()],
                          bid_strategy="cpm",
                          bid=100.0)
        adgroup.put()

        self.creative = HtmlCreative(key_name="key_name",
                                     name="image dummy",
                                     ad_type="html",
                                     html_data="<html>test mraid data</html>",
                                     format="full",
                                     format_predicates=["format=320x50"],
                                     tracking_url="http://www.google.com/pingme",
                                     ad_group=adgroup,
                                     ormma_html=True,
                                     launchpage="http://www.google.com2/")

        self.creative.image_width = 320
        self.creative.image_height = 50
        self.creative.put()

        _on_fail_exclude_adgroups = [e for e in self.on_fail_exclude_adgroups]
        self.on_fail_exclude_adgroups = []

        # For this test we want to makes sure that the templates
        # are correct for fullscreen tablets
        # (i.e. the meta tag)
        self.adunit.format = 'full'
        old_format = self.adunit.format

        self._compare_rendering_with_examples("mraid_full", suffix="")

        self.adunit.format = old_format

        self.on_fail_exclude_adgroups = _on_fail_exclude_adgroups


    # image, text and text_icon adtypes are not tested as defaults
    def mptest_image_adtype(self):
        """ Make a one-off test for image creatives. """
        self.creative = ImageCreative(key_name="key_name",
                                      name="image dummy",
                                      image_blob="blobby",
                                      url="http://www.google.com",
                                      ad_type="image",
                                      format="320x50",
                                      format_predicates=["format=320x50"],
                                      ad_group=self.adgroup)

        self.creative.image_width = 320
        self.creative.image_height = 50
        self.creative.put()

        self.creative.image_url = 'http://localhost:8080/_ah/img/blobby=s0'

        self._compare_rendering_with_examples("image_adtype", suffix="")

    # def mptest_text_adtype(self):
    #     """ Make a one-off test for image creatives. """
    #     self.creative = TextCreative(key_name="key_name",
    #                                  name="image dummy",
    #                                  headline="HEADLINE!!",
    #                                  line1="Sweet line",
    #                                  line2="Awesome line",
    #                                  ad_type="text",
    #                                  format="320x50",
    #                                  format_predicates=["format=320x50"],
    #                                  ad_group=self.adgroup)
    #     self.creative.put()
    #
    #     self._compare_rendering_with_examples("text_adtype", suffix="")

    def mptest_text_icon_adtype(self):
        """ Make a one-off test for image creatives. """
        self.creative = TextAndTileCreative(key_name="key_name",
                                            name="image dummy",
                                            image_blob="blobby",
                                            line1="Sweet line",
                                            line2="Awesome line",
                                            url="http://www.google.com",
                                            ad_type="text_icon",
                                            format="320x50",
                                            format_predicates=["format=320x50"],
                                            ad_group=self.adgroup)


        self.creative.put()

        self.creative.image_url = 'http://localhost:8080/_ah/img/blobby=s0'

        self._compare_rendering_with_examples("text_icon_adtype", suffix="")

    def mptest_macro_test(self):
        mega_macro = CLK_URL + '\n' + CLK_URL_ESC + '\n' + CACHEBUSTER + '\n' + \
                     ADGROUP_ID + '\n' + CREATIVE_ID + '\n' + CLK_THRU + '\n' + \
                     CLK_THRU + '\n' + CLK_THRU_ESC + '\n' + CLK_THRU_2ESC + '\n' + \
                     UDID

        self.creative = HtmlCreative(key_name = 'key_name',
                                     name = 'macrowned',
                                     url = 'http://www.mopub.com',
                                     ad_type = 'html',
                                     format = '320x50',
                                     ad_group = self.adgroup,
                                     html_data = mega_macro,
                                     )
        self.creative.put()
        self._compare_rendering_with_examples('mega_macrooo', suffix = '')


##### TEST GENERATORS ######

NETWORK_NAMES = ("admob",
                 "jumptap",
                 "ejam",
                 "chartboost",
                 "millennial",
                 "inmobi",
                 "greystripe",
                 "appnexus",
                 "mobfox",
                 "custom",

                 "adsense",
                 "brightroll",

                 "custom_native",
                 "admob_native",
                 "millennial_native",
                 "iAd",
                 )



def mptest_full_network_generator():
    """ Uses Nose's built in generator system to run multiple tests.
        Tests each of the network's default creatives, """
    test = RenderingTestBase()

    for network_name in NETWORK_NAMES:
        test.setUp()
        yield test.render_full_creative, network_name
        test.tearDown()

def mptest_320x50_network_generator():
    """ Uses Nose's built in generator system to run multiple tests. """
    test = RenderingTestBase()
    for network_name in NETWORK_NAMES:
        test.setUp()
        yield test.render_320x50_creative, network_name
        test.tearDown()







