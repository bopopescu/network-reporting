# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('network_scraping.views',
        url(r'^$', 'adnetwork_report_index', name='adnetwork_reports_index'),
        url(r'^app_view/(?P<ad_network_app_mapper_key>[-\w\.]+)/$', 'view_adnetwork_app_report', name='view_adnetwork_app_report')
        )