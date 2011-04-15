# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('reports.views',
        url(r'^view/$', 'request_report', name='request_report'),
        url(r'^view/(?P<report_key>[-\w\.]+)/$', 'view_report', name='view_report'),
        url(r'^$', 'report_index', name='reports_index'),
        url(r'^check/(?P<report_key>[-\w\.]+)/$', 'check_report', name='check_report'),
        url(r'^gen_report/$', 'gen_report', name='generate_reports'),
        url(r'^add/$', 'add_report', name='add_report')
        )
