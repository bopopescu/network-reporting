# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('publisher.views',
  url(r'^create$','create',name='publisher_create'),
  url(r'^update$','update',name='publisher_update'),
  url(r'^generate$','generate',name='publisher_generate'),
  url(r'^show$','show',name='publisher_show'),
  url(r'^$','index',name='publisher_index'),
)
