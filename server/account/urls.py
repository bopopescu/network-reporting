# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('account.views',
    url(r'^$','index', name='account_index'),
    url(r'^networks/$','ad_network_settings', name='ad_network_settings'),
    url(r'^payments/history$', 'payment_history', name='payment_history'),
    url(r'^payments/change$','payment_info_change', name='payment_info_change'),
    url(r'^new/$','new', name='account_new'),
    url(r'^logout/$','logout', name='account_logout'),
)
