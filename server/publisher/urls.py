# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'publisher.views',
    url(r'^$', 'app_index', name='app_index'),
    url(r'^dashboard/', 'dashboard', name='dashboard'),

    url(r'^app/create/$', 
        'create_app',
        name='publisher_create_app'),
    
    url(r'^app/(?P<app_key>[-\w\.]+)/delete/$',
        'delete_app',
        name='publisher_delete_app'),
    
    url(r'^app/(?P<app_key>[-\w\.]+)/update/ajax/$',
        'app_update_ajax',
        name='publisher_app_update_ajax'),
    
    url(r'^app/(?P<app_key>[-\w\.]+)/$',
        'app_detail',
        name='publisher_app_show'),

    url(r'^adunit/(?P<adunit_key>[-\w\.]+)/delete/$',
        'delete_adunit',
        name='publisher_delete_adunit'),
    
    url(r'^adunit/(?P<adunit_key>[-\w\.]+)/generate/$',
        'integration_help',
        name='publisher_integration_help'),
    
    url(r'^adunit/update/ajax/$',
        'adunit_update_ajax',
        name='publisher_adunit_update_ajax'),
    
    url(r'^adunit/(?P<adunit_key>[-\w\.]+)/$',
        'adunit_detail',
        name='publisher_adunit_show'),

    # Exporting

    url(r'^export/inventory/$',
        'inventory_exporter',
        name='publisher_inventory_exporter'),
    
    url(r'^export/app/(?P<app_key>[-\w\.]+)/$',
        'app_exporter',
        name='publisher_app_exporter'),

    url(r'^export/adunit/(?P<adunit_key>[-\w\.]+)/$',
        'adunit_exporter',
        name='publisher_adunit_exporter'),
)
