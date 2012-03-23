# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    # view module
    'advertiser.views',

    #############
    # Creatives #
    #############
    
    url(r'^creative/create/$',
        'creative_create',
        name='advertiser_creative_create'),
    
    url(r'^creative/manage/$',
        'creative_manage',
        name='advertiser_creative_manage'),
    
    url(r'^creative/image/(?P<creative_key>[-\w\.]+)$',
        'creative_image',
        name='advertiser_creative_image'),
    
    url(r'^creative/html/(?P<creative_key>[-\w\.]+)$',
        'creative_html',
        name='advertiser_creative_html'),

    ##############
    # Deprecated #
    ##############
    
    #REFACTOR: is this needed? remove if not
    url(r'^bid/pause/$',
        'bid_pause',
        name='advertiser_bid_pause'),

    #REFACTOR: is this needed? remove if not
    url(r'^adserver_test/$',
        'adserver_test',
        name='advertiser_adserver_test'),

    #REFACTOR: replace this if possible
    url(r'^export/$',
        'campaign_export',
        name='campaign_export'),

    #REFACTOR: remove this if possible
    url(r'^mpx/$',
        'mpx_info',
        name='mpx_info'),
    
    # Networks, in the process of deprecating
    url(r'^networks/$', 'network_index', name='network_index'),

    ###############
    # Marketplace #
    ###############
    
    url(r'^marketplace/$',
        'marketplace_index',
        name='marketplace_index'),
    
    url(r'^marketplace/creatives/$',
        'marketplace_creative_proxy',
        name='marketplace_creatives'),
    
    url(r'^marketplace/activation/$',
        'marketplace_on_off',
        name='marketplace_on_off'),
    
    url(r'^marketplace/settings/blindness/$',
        'marketplace_blindness_change',
        name='marketplace_blindness_change'),
    
    url(r'^marketplace/settings/blocklist/$',
        'marketplace_blocklist_change',
        name='marketplace_blocklist_change'),
    
    url(r'^marketplace/settings/content_filter/$',
        'marketplace_content_filter',
        name='marketplace_content_filter'),


    ###############
    # Direct sold #
    ###############


    # Top level indexes
    url('^orders/$',
        'order_index',
        name='advertiser_order_index'),

    url('^line_items/$',
        'line_item_index',
        name='advertiser_line_item_index'),

    
    # Forms
    # Note: these need to come before the detail
    # pages, or else the wrong handler will be called.
    # ('new' will be interpreted as an order/line item key)
    url('^orders/(?P<order_key>[-\w\.]+)/edit/$',
        'order_form',
        name='advertiser_order_form_edit'),
    
    url('^orders/new/$',
        'order_and_line_item_form',
        name='advertiser_order_and_line_item_form_new'),


    url('^orders/(?P<order_key>[-\w\.]+)/line_items/new/$',
        'order_and_line_item_form',
        name='advertiser_line_item_form_new'),


    url('^line_items/(?P<line_item_key>[-\w\.]+)/edit/$',
        'order_and_line_item_form',
        name='advertiser_line_item_form_edit'),


    # Detail pages
    url('^orders/(?P<order_key>[-\w\.]+)/$',
        'order_detail',
        name='advertiser_order_detail'),
    
    url('^line_items/(?P<line_item_key>[-\w\.]+)/$',
        'line_item_detail',
        name='advertiser_line_item_detail'),

    # Status changing (active/pause/archive)
    url('^ad_source/status/$',
        'ad_source_status_change'),
)
