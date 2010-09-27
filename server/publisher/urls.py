# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('publisher.views',
  url(r'^adunit/$','show',name='publisher_show'),
  url(r'^adunit/create/$','create',name='publisher_create'),
  url(r'^adunit/edit/$','update',name='publisher_update'),
  url(r'^adunit/generate/$','generate',name='publisher_generate'),
  url(r'^adunit/delete/$','generate',name='publisher_delete'),
  url(r'^app/$','app_show',name='publisher_app_show'),
  url(r'^create/$','app_create',name='publisher_app_create'),
  url(r'^edit/$','app_update',name='publisher_app_update'),
  url(r'^getartwork/$','getartwork',name='publisher_getartwork'),
  url(r'^$','index',name='publisher_index'),
)
