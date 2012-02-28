from ad_server.networks.appnexus import AppNexusServerSide
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

from advertiser.models import DummyServerSideFailureCreative, DummyServerSideSuccessCreative


SERVERSIDE_DICT = {
     "appnexus":AppNexusServerSide,
     "brightroll":BrightRollServerSide,
     "ejam":EjamServerSide,
     "chartboost":ChartBoostServerSide,
     "mobfox":MobFoxServerSide,
     "greystripe":GreyStripeServerSide,
     "jumptap":JumptapServerSide,
     "inmobi":InMobiServerSide,
     "millennial": MillennialServerSide,
}


def get_serverside_for_creative(creative):
    nn = creative.network_name
    if nn and nn in SERVERSIDE_DICT:
        return SERVERSIDE_DICT[nn]
    elif isinstance(creative, DummyServerSideFailureCreative):
        return DummyServerSideFailure
    elif isinstance(creative, DummyServerSideSuccessCreative):
        return DummyServerSideSuccess
    else:
        return None
