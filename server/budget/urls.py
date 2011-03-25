# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('budget.views',
  url(r'^advance/$','budget_advance',name='budget_advance'),
  url(r'^campaign_logs/(?P<campaign_key>.*)/$','budget_logs',name='budget_campaign_logs'),
)
