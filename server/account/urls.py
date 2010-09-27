# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('account.views',
  url(r'^$','index',name='account_index'),
  url(r'^logout/$','logout',name='account_logout'),
  url(r'^test/$','test',name='account_test'),
  url(r'^test2/$','test2',name='account_test2'),
)
