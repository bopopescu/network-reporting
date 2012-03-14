# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('advertiser.views',

    url(r'^creative/create/$', 'creative_create', name='advertiser_creative_create'),
    url(r'^creative/manage/$', 'creative_manage', name='advertiser_creative_manage'),
    url(r'^creative/image/(?P<creative_key>[-\w\.]+)$', 'creative_image', name='advertiser_creative_image'),
    url(r'^creative/html/(?P<creative_key>[-\w\.]+)$', 'creative_html', name='advertiser_creative_html'),
    url(r'^bid/pause/$', 'bid_pause', name='advertiser_bid_pause'),

    url(r'^adserver_test/$', 'adserver_test', name='advertiser_adserver_test'),

    url(r'^export/$', 'campaign_export', name='campaign_export'),
    url(r'^mpx/$', 'mpx_info', name='mpx_info'),

    # Networks (in the process of deprecating)
    url(r'^networks/$', 'network_index', name='network_index'),

    # Marketplace
    url(r'^marketplace/$', 'marketplace_index', name='marketplace_index'),
    url(r'^marketplace/creatives/$', 'marketplace_creative_proxy', name='marketplace_creatives'),
    url(r'^marketplace/activation/$', 'marketplace_on_off', name='marketplace_on_off'),
    url(r'^marketplace/settings/blindness/$', 'marketplace_blindness_change', name='marketplace_blindness_change'),
    url(r'^marketplace/settings/blocklist/$', 'marketplace_blocklist_change', name='marketplace_blocklist_change'),
    url(r'^marketplace/settings/content_filter/$', 'marketplace_content_filter', name='marketplace_content_filter'),


    # Order/LineItem urls
    url('^orders/$', 'order_index', name='advertiser_order_index'),

    url('^orders/new/$', 'order_form', name='advertiser_order_form_new'),
    url('^orders/(?P<campaign_key>[-\w\.]+)/$', 'order_detail', name='advertiser_order_detail'),
    url('^orders/(?P<order_key>[-\w\.]+)/edit/$', 'order_form', name='advertiser_order_form_edit'),

    url('^orders/(?P<order_key>[-\w\.]+)/line_items/new/$', 'line_item_form', name='advertiser_line_item_form_new'),
    url('^orders/(?P<campaign_key>[-\w\.]+)/line_items/(?P<adgroup_key>[-\w\.]+)/$', 'lineitem_detail', name='advertiser_lineitem_detail'),
    url('^orders/(?P<order_key>[-\w\.]+)/line_items/(?P<line_item_key>[-\w\.]+)/edit/$', 'line_item_form', name='advertiser_line_item_form_edit'),

)
