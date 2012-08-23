# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'api.views',

    ########
    # APPS #
    ########

    # all apps for an account
    url(r'^app/$',
        'app_service',
        name='app_service'),

    # specific app
    url(r'^app/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='app_service'),

    # a single app targeted by an adgroup
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)/apps/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='adgroup_app_service'),

    # a single app targeted by a campaign (possibly multiple adgroups)
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)/apps/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='app_service'),

    ###########
    # ADUNITS #
    ###########

    # all adunits
    url(r'^adunits/(?P<adunit_key>[-\w\.]+)$',
        'adunit_service',
        name='adunit_service'),

    # specific adunit
    url(r'^adunits/(?P<adunit_key>[-\w\.]+)$',
        'adunit_service',
        name='adunit_service'),

    # specific adunit for an app
    # same thing as /adunits/<adunit_key>/
    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/(?P<adunit_key>[-\w\.]+)$',
        'adunit_service',
        name='app_adunit_service'),

    # all adunits for an app
    url(r'^app/(?P<app_key>[-\w\.]+)/adunits/$',
        'adunit_service',
        name='app_adunit_service'),


    # all adunits targeted by an adgroup
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)/adunits/$',
        'adunit_service',
        name='adgroup_adunit_service'),

        # all adunits targeted by an adgroup
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)/adunits/(?P<adunit_key>[-\w\.]+)$',
        'adunit_service',
        name='adgroup_adunit_service'),

    # all adunits targeted by an individual campaign
    # (possibly with multiple adgroups)
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)/adunits/$',
        'adunit_service',
        name='adunit_service'),

    # an individual adunit targeted by an individual campaign
    # (possibly with multiple adgroups)
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)/adunits/(?P<adunit_key>[-\w\.]+)$',
        'adunit_service',
        name='adunit_service'),

    ############
    # ADGROUPS #
    ############

    # # all adgroups for an account
    # url(r'^adgroup/$',
    #     'adgroup_service',
    #     name='adgroup_service'),

    # specific adgroup for an account
    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)$',
        'adgroup_service',
        name='adgroup_service'),

    #############
    # CAMPAIGNS #
    #############

    # # all campaigns and adgroups for an account
    # url(r'^campaign/$',
    #     'campaign_service',
    #     name='campaign_service'),

    # a single campaign with all of its adgroups
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)$',
        'campaign_service',
        name='campaign_service'),

    # /api/campaign/<campaign_key>/adunits
    # all adunit stats for a campaign
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)/adunits/$',
        'adunit_service',
        name='campaign_adunit_service'),

    # /api/adgroup/<adgroup_key/apps/<app_key>
    # individual app from a campaign
    url(r'^campaign/(?P<campaign_key>[-\w\.]+)/apps/(?P<app_key>[-\w\.]+)$',
        'app_service',
        name='campaign_app_service'),

    # TODO: make subdomain networks.mopub.com
    # networks api
    url(r'^networks/$',
        'networks_api',
        name='networks_api'),

    # TODO: remove when migration to new networks is done

    ############
    # NETWORKS #
    ############
    #REFACTOR: move somewhere else

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
