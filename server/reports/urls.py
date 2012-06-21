# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('reports.views',
        url(r'^view/$', 'request_report', name='request_report'),
        url(r'^$', 'reports_index', name='reports_index'),
        url(r'^check/(?P<report_key>[-\w\.]+)/$', 'check_report', name='check_report'),
        url(r'^add/$', 'edit_report', name='add_report'),
        url(r'^edit/(?P<report_key>[-\w\.]+)/$', 'edit_report', name='edit_report'),
        url(r'^run/(?P<report_key>[-\w\.]+)/$', 'run_report', name='run_report'),
        url(r'^save/(?P<report_key>[-\w\.]+)/$', 'save_report', name='save_report'),
        url(r'^daily_sched_runner/$', 'sched_runner', name='sched_runner'),
        url(r'^export/(?P<report_key>[-\w\.]+)/$', 'exporter', name='report_export'),
        url(r'^update_report_state/$', 'update_report_state', name='report_state_change'),
        )
