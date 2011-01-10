# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('exchange.views',
  url(r'^schedule/$','schedule',name='exchange_schedule'),
  url(r'^$','index',name='exchange_index'),
)
