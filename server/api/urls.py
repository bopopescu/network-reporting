# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'api.views',

    # /api/app/<app_key>
    # all adunits for an account
    url(r'^app/$',
        'app_service',
        name='app_service'),

    # /api/app/<app_key>
    # specific adunits for an account
    url(r'^app/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='app_service'),

    # /api/app/<app_key>/adunits/
    # all adunits for an app
    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/$',
        'adunit_service',
        name='app_adunit_service'),

    # /api/app/<app_key>/adunits/<adunit_key>
    # specific adunits for an app
    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/(?P<adunit_key>[-\w\.]+)$',
        'adunit_service',
        name='adunit_service'),

    # /api/adgroup/
    # all adgroups for an account
    url(r'^adgroup/$',
        'adgroup_service',
        name='adgroup_service'),

    # /api/adgroup/<adgroup_key>
    # specific adgroup for an account
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)$',
        'adgroup_service',
        name='adgroup_service'),

    # /api/adgroup/<adgroup_key/adunits/
    # all adunits from an adgroup
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)/adunits/$',
        'adunit_service',
        name='adgroup_adunit_service'),

    # /api/adgroup/<adgroup_key/apps/<app_key>
    # individual app from an adgroup
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)/apps/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='adgroup_app_service'),

    # /api/campaign/<campaign_key>
    # individual campaign
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)$',
        'campaign_service',
        name='campaign_service'),

    # /api/adgroup/<adgroup_key/apps/<app_key>
    # individual app from an adgroup
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)/apps/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='campaign_app_service'),

    # TODO: make subdomain networks.mopub.com
    # networks api
    url(r'^networks/$',
        'networks_api',
        name='networks_api'),

    #TODO: remove /api/network_apps
    # /api/network_apps/<network>
    # all app stats for the network
    url(r'^network_apps/(?P<campaign_key>[-\w\.]+)$',
        'network_apps_service',
        name='network_apps_service'),

    # /api/network_apps/<network>/adunits
    # all app stats for the network including adunits
    url(r'^network_apps/(?P<campaign_key>[-\w\.]+)/(?P<adunits>adunits)$',
        'network_apps_service',
        name='network_apps_service'),

    # TODO: remove when migration to new networks is done
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
