# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template


urlpatterns = patterns('website.views',
  url(r'^main/$', direct_to_template,{'template': 'website/index.html'},name='website_main'),     
  url(r'^about/$',direct_to_template,{'template': 'website/about.html'},name='website_about'),   
  url(r'^$', 'website_splash', name='website_splash'),
  url(r'^splash/$', 'website_splash', name='website_splash'),   
  url(r'^splash/join/$', 'website_join', name='website_join')
)
