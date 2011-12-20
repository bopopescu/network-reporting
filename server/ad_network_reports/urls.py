# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('ad_network_reports.views',
        url(r'^$',
            'ad_network_reports_index',
            name='ad_network_reports_index'),

        url(r'^app_view/(?P<mapper_key>[-\w\.]+)/$',
            'app_detail',
            name='ad_network_app_detail'),

        url(r'^manage/$',
            'ad_network_management',
            name='manage_ad_network_reports'),
        )
