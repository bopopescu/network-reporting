# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('advertiser.views',
    url(r'^create/$', 'create_campaign_and_adgroup', name='advertiser_campaign_create'),
    url(r'^edit/(?P<adgroup_key>[-\w\.]+)/$', 'edit_campaign_and_adgroup', name='advertiser_campaign_edit'),

    url(r'^creative/create/$', 'creative_create', name='advertiser_creative_create'),
    url(r'^creative/manage/$', 'creative_manage', name='advertiser_creative_manage'),
    url(r'^creative/image/(?P<creative_key>[-\w\.]+)$', 'creative_image', name='advertiser_creative_image'),
    url(r'^creative/html/(?P<creative_key>[-\w\.]+)$', 'creative_html', name='advertiser_creative_html'),
    url(r'^bid/pause/$', 'bid_pause', name='advertiser_bid_pause'),

    url(r'^adgroup/(?P<adgroup_key>[-\w\.]+)/$', 'campaign_adgroup_show', name='advertiser_adgroup_show'),
    url(r'^adserver_test/$', 'adserver_test', name='advertiser_adserver_test'),

    url(r'^$', 'adgroups', name='advertiser_campaign'),
    url(r'^archive/$', 'archive', name='advertiser_archive'),
    url(r'^export/$', 'campaign_export', name='campaign_export'),
    url(r'^mpx/$', 'mpx_info', name='mpx_info'),

    url(r'^networks/$', 'network_index', name='network_index'),

    url(r'^marketplace/$', 'marketplace_index', name='marketplace_index'),
    url(r'^marketplace/creatives/$', 'marketplace_creative_proxy', name='marketplace_creatives'),
    url(r'^marketplace/activation/$', 'marketplace_on_off', name='marketplace_on_off'),
    url(r'^marketplace/settings/blindness/$', 'marketplace_blindness_change', name='marketplace_blindness_change'),
    url(r'^marketplace/settings/blocklist/$', 'marketplace_blocklist_change', name='marketplace_blocklist_change'),
    url(r'^marketplace/settings/content_filter/$', 'marketplace_content_filter', name='marketplace_content_filter'),


    # Order/LineItem urls
    url('^$', 'order_index', name='advertiser_order_index'),
    url('^$', 'order_detail', name='advertiser_order_detail'),
    url('^$', 'order_form', name='advertiser_order_form'),

    url('^$', 'lineitem_detail', name='advertiser_lineitem_detail'),
    url('^$', 'lineitem_archive', name='advertiser_lineitem_archive'),
    url('^$', 'lineitem_form', name='advertiser_lineitem_form'),
)
