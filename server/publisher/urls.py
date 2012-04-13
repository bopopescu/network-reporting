# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'publisher.views',
    url(r'^$', 'app_index', name='app_index'),
    url(r'^dashboard/', 'dashboard', name='dashboard'),
    url(r'^geo$', 'geo_performance', name='publisher_geo_performance'),

    url(r'^app/create/$', 'create_app', name='publisher_create_app'),
    url(r'^app/(?P<app_key>[-\w\.]+)/delete/$', 'delete_app', name='publisher_delete_app'),
    url(r'^app/(?P<app_key>[-\w\.]+)/update/ajax/$', 'app_update_ajax', name='publisher_app_update_ajax'),
    url(r'^app/(?P<app_key>[-\w\.]+)/$', 'app_detail', name='publisher_app_show'),

    url(r'^adunit/create/$', 'create_adunit', name='publisher_create_adunit'),
    url(r'^adunit/(?P<adunit_key>[-\w\.]+)/delete/$', 'delete_adunit', name='publisher_delete_adunit'),
    url(r'^adunit/(?P<adunit_key>[-\w\.]+)/generate/$', 'integration_help', name='publisher_integration_help'),
    url(r'^adunit/update/ajax/$', 'adunit_update_ajax', name='publisher_adunit_update_ajax'),
    url(r'^adunit/(?P<adunit_key>[-\w\.]+)/$', 'adunit_show', name='publisher_adunit_show'),

    url(r'^export/(?P<f_type>xls|csv)/(?P<key_type>adunit|app|adgroup|account)/(?P<key>[-\w\.]+)/$', 'export_file', name='exporter'),
    url(r'^app_export$', 'app_export', name='publisher_app_export'),
    url(r'^dashboard_export$', 'dashboard_export', name='dashboard_export'),
)
