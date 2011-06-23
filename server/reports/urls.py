# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('reports.views',
        url(r'^view/$', 'request_report', name='request_report'),
        url(r'^view/(?P<report_key>[-\w\.]+)/$', 'view_report', name='view_report'),
        url(r'^$', 'report_index', name='reports_index'),
        url(r'^check/(?P<report_key>[-\w\.]+)/$', 'check_report', name='check_report'),
        #Gen report is called by the TQ
        url(r'^gen_report/$', 'gen_report', name='generate_reports'),
        #Add report is when you want to make a new report
        url(r'^add/$', 'add_report', name='add_report'),
        url(r'^run/(?P<report_key>[-\w\.]+)/$', 'run_report', name='run_report'),
        url(r'^save/(?P<report_key>[-\w\.]+)/$', 'save_report', name='save_report'),
        url(r'^daily_sched_runner/$', 'sched_runner', name='sched_runner'),
        url(r'^export/$', 'exporter', name='report_export'),
        )
