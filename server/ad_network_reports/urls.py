# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('ad_network_reports.views',
        url(r'^$', 'ad_network_report_index', name='ad_network_reports_index'),
        url(r'^add/$', 'add_login_credentials', name='add_login_credentials'),
        url(r'^app_view/(?P<ad_network_app_mapper_key>[-\w\.]+)/$',
            'view_ad_network_app_report', name='view_ad_network_app_report'),
        url(r'^manage/$', 'manage_ad_network_reports',
            name='manage_ad_network_reports'),
        url(r'^manage/(?P<account_key>[-\w\.]+)/$', 'ad_network_report_index',
                name='manage_ad_network_reports_index'),
        url(r'^manage/(?P<account_key>[-\w\.]+)/add/$', 'add_login_credentials',
            name='manage_add_login_credentials')
        )
