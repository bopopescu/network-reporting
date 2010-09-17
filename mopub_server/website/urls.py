# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template


urlpatterns = patterns('website.views',
  url(r'^main/$', direct_to_template,{'template': 'website/index.html'}),     
  url(r'^about/$',direct_to_template,{'template': 'website/about.html'}),   
  url(r'^splash/$',direct_to_template,{'template': 'website/splash.html'}),   
)
