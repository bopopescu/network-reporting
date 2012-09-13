# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('ad_network_reports.views',
        url(r'^login_state/$',
            'login_state',
            name='login_state'),

        url(r'^create_mapper/$',
            'create_mapper',
            name='create_mapper'),

        url(r'^settings/$',
            'ad_network_settings',
            name='ad_network_reports_settings'),

        url(r'^manage/$',
            'ad_network_management',
            name='manage_ad_network_reports'),
        )
