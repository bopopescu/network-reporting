# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('website.views',
  url(r'^welcome$', 'website_welcome', name='website_welcome'),
  url(r'^$', 'website_root', name='website_root'),
)
