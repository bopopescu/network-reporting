# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('account.views',
    url(r'^$','index',name='account_index'),
    url(r'^new/$','new',name='account_new'),
    url(r'^logout/$','logout',name='account_logout'),
)
