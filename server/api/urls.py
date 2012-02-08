# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'api.views',

    # /api/app/<app_key>
    url(r'^app/$',
        'app_service',
        name='app_service'),

    url(r'^app/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='app_service'),

    # /api/app/<app_key>/adunits/<adunit_key>
    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/$',
        'adunit_service',
        name='adunit_service'),

    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/(?P<adunit_key>[-\w\.]+)$',
        'adunit_service',
        name='adunit_service'),

    # /api/adgroup/<adgroup_key>
    url(r'^adgroup/$',
        'adgroup_service',
        name='adgroup_service'),

    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)$',
        'adgroup_service',
        name='adgroup_service'),




    url(r'^ad_network/account_roll_up/$',
        'account_roll_up_service',
        name='account_roll_up_service'),

    url(r'^ad_network/daily_stats/$',
        'daily_stats_service',
        name='daily_stats_service'),

    url(r'^ad_network/roll_up/(?P<type_>app|network)/id/(?P<id_>[-\w\.]+)$',
        'roll_up_service',
        name='roll_up_service'),

    url(r'^ad_network/app_on_network/(?P<network>[-\w\.]+)/pub_id/(?P<pub_id>[-\w\.]+)$',
        'app_on_network_service',
        name='app_on_network_service'),
)
