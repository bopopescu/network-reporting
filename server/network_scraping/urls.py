# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('adnetwork_reports.views',
        url(r'^$', 'adnetwork_report_index', name='adnetwork_reports_index'),
        url(r'^view/(?P<app_key>[-\w\.]+)/$', 'view_adnetwork_report', name='view_adnetwork_report')
        )