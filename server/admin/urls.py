# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('admin.views',
  url(r'^switch_user/$','admin_switch_user',name='admin_switch_user'),
  url(r'^d/$', 'dashboard', name='dashboard'),
  url(r'^report/$', 'report', name='report')
)
