# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('budget.views',
    url(r'^advance/$','budget_advance',name='budget_advance'),
    url(r'^daily_advance/$','daily_budget_advance',name='budget_daily_advance'),
    url(r'^advance_worker/$','advance_worker',name='budget_advance_worker'),
    url(r'^daily_advance_worker/$','daily_advance_worker',name='budget_daily_advance_worker'),
    url(r'^view/(?P<adgroup_key>.*)/$','budget_view',name='budget_view'),
)
