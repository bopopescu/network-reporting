# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('admin.views',
  url(r'^switch_user/$','admin_switch_user',name='admin_switch_user'),
  url(r'^prep/$', 'dashboard_prep', name="dashboard_prep"),
  url(r'^d/$', 'dashboard', name='admin_dashboard'),
  url(r'^sfdc/$', 'update_sfdc_leads', name='update_sfdc_leads'),
  url(r'^migrate_image/$','migrate_image', name='admin_migrate_image'),
)
