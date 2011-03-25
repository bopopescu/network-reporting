# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('budget.views',
    url(r'^advance/$','budget_advance',name='budget_advance'),
    url(r'^campaign_logs/(?P<campaign_key>.*)/$','budget_logs',name='budget_campaign_logs'),
    url(r'^campaign_budget/(?P<campaign_key>.*)/$','mem_budget',name='budget_campaign_budget'),
    url(r'^set_budget/(?P<campaign_key>.*)/$','set_budget',name='budget_set_budget'),
)
