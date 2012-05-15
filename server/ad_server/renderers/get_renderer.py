from ad_server.renderers.admob import AdMobRenderer
from ad_server.renderers.admob_native import AdMobNativeRenderer
from ad_server.renderers.adsense import AdSenseRenderer
from ad_server.renderers.appnexus import AppNexusRenderer
from ad_server.renderers.base_html_renderer import BaseHtmlRenderer
from ad_server.renderers.brightroll import BrightRollRenderer
from ad_server.renderers.chartboost import ChartBoostRenderer
from ad_server.renderers.creative_renderer import BaseCreativeRenderer
from ad_server.renderers.custom_native import CustomNativeRenderer
from ad_server.renderers.ejam import EjamRenderer
from ad_server.renderers.greystripe import GreyStripeRenderer
from ad_server.renderers.html_data_renderer import HtmlDataRenderer
from ad_server.renderers.iad import iAdRenderer
from ad_server.renderers.inmobi import InmobiRenderer
from ad_server.renderers.image import ImageRenderer
from ad_server.renderers.jumptap import JumptapRenderer
from ad_server.renderers.millennial_native import MillennialNativeRenderer
from ad_server.renderers.millennial import MillennialRenderer
from ad_server.renderers.mobfox import MobFoxRenderer
from ad_server.renderers.text_and_tile import TextAndTileRenderer

from advertiser.models import (ImageCreative,
                               HtmlCreative,
                               TextAndTileCreative)

RENDERERS = {
     "mobfox":MobFoxRenderer,
     "greystripe":GreyStripeRenderer,
     "jumptap":JumptapRenderer,
     "brightroll":BrightRollRenderer,
     "appnexus":AppNexusRenderer,
     "inmobi":InmobiRenderer,
     "ejam":ChartBoostRenderer,
     "chartboost":ChartBoostRenderer,
     "millennial_native": MillennialNativeRenderer,
     "millennial": MillennialRenderer,
     "admob_native": AdMobNativeRenderer,
     "admob": AdMobRenderer,
     "adsense": AdSenseRenderer,
     "iAd": iAdRenderer,
     "custom_native": CustomNativeRenderer,
     "custom": HtmlDataRenderer,
}

def get_renderer_for_creative(creative):
    if creative.network_name:
        return RENDERERS[creative.network_name]
    else:
        if isinstance(creative, ImageCreative):
            return ImageRenderer
        elif isinstance(creative, HtmlCreative):
            return HtmlDataRenderer
        elif isinstance(creative, TextAndTileCreative):
            return TextAndTileRenderer
        else:
            assert False, "We do not have an appropriate renderer for Creative type %s. Defaulting to BaseCreativeRenderer, which will probably raise an exception if used." % type(creative)
            return BaseCreativeRenderer
