# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns(
    # view module
    'advertiser.views',

    ##############
    # Deprecated #
    ##############

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


    # Top level entry point
    url('^orders/$',
        'order_index',
        name='advertiser_order_index'),

    # Status changing (active/pause/archive)
    url('^ad_source/status/$',
        'ad_source_status_change',
        name='advertiser_ad_source_status_change'),

    # Forms
    # Note: these need to come before the detail
    # pages, or else the wrong handler will be called.
    # ('new' will be interpreted as an order/line item key)

    url('^orders/new/$',
        'order_and_line_item_form_new_order',
        name='advertiser_order_and_line_item_form_new'),

    url('^orders/(?P<order_key>[-\w\.]+)/edit/$',
        'order_form',
        name='advertiser_order_form_edit'),

    url('^orders/(?P<order_key>[-\w\.]+)/new_line_item/$',
        'order_and_line_item_form_new_line_item',
        name='advertiser_line_item_form_new'),

    url('^line_items/(?P<line_item_key>[-\w\.]+)/edit/$',
        'order_and_line_item_form_edit',
        name='advertiser_line_item_form_edit'),

    url('^line_items/(?P<line_item_key>[-\w\.]+)/new_creative/$',
        'creative_form_new',
        name='advertiser_creative_form_new'),

    url('^creatives/(?P<creative_key>[-\w\.]+)/edit/$',
        'creative_form_edit',
        name='advertiser_creative_form_edit'),

    # Detail pages
    url('^orders/(?P<order_key>[-\w\.]+)/$',
        'order_detail',
        name='advertiser_order_detail'),

    url('^line_items/(?P<line_item_key>[-\w\.]+)/$',
        'line_item_detail',
        name='advertiser_line_item_detail'),

    url('^creative/image/(?P<creative_key>[-\w\.]+)$',
        'creative_image',
        name='advertiser_creative_image'),

    url('^creative/html/(?P<creative_key>[-\w\.]+)$',
        'creative_html',
        name='advertiser_creative_html'),

    #############
    # Exporting #
    #############

    url('^export/orders/$',
        'export_multiple_orders',
        name='advertiser_export_multiple_orders'),

    url('^export/order/$',
        'export_single_order',
        name='advertiser_export_single_order'),

    url('^export/lineitems/$',
        'export_multiple_line_items',
        name='advertiser_export_multiple_line_items'),

    url('^export/lineitem/$',
        'export_single_line_item',
        name='advertiser_export_single_line_item'),
)
