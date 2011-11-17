# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'api.views',
    url(r'^app/$', 'app_service', name='app_service'),
    url(r'^app/(?P<app_key>[-\w\.]+)$', 'app_service', name='app_service'),

    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/$', 'adunit_service', name='adunit_service'),
    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/(?P<adunit_key>[-\w\.]+)$', 'adunit_service', name='adunit_service'),

    url(r'^adgroup/$', 'adgroup_service', name='adgroup_service'),
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)$', 'adgroup_service', name='adgroup_service'),

    url(r'^campaign/$', 'campaign_service', name='campaign_service'),
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)$', 'campaign_service', name='campaign_service'),

    url(r'^network_campaign/$', 'network_campaign_service', name='network_campaign_service'),
    url(r'^campaign/network/(?P<network_campaign_key>[-\w\.]+)$', 'network_campaign_service', name='network_campaign_service'),

    url(r'^creatives/$', 'creative_service', name='creative_service'),
    url(r'^creatives/(?P<creative_key>[-\w\.]+)$', 'creative_service', name='creative_service'),

    url(r'^dsp/$', 'dsp_service', name='dsp_service'),
    url(r'^dsp/(?P<dsp_key>[-\w\.]+)$', 'dsp_service', name='dsp_service'),
)
