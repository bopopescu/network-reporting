# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from common.constants import (  MARKET_SEARCH_KEY,
                                )


urlpatterns = patterns('website.views',
  url(r'^main$', direct_to_template,{'template': 'website/index.html'},name='website_main'),
  url(r'^welcome$', direct_to_template,{'template': 'website/welcome.html'},name='website_welcome'),
  url(r'^about$', direct_to_template,{'template': 'website/about.html'},name='website_about'),
  url(r'^$', 'website_root', name='website_root'),
  url(r'^splash/join/$', 'website_join', name='website_join'),
  url(r'^pending/$', 'website_pending', name='website_pending'),
  url( r'^android_market_search/(?P<qs>.*?)/$', 'droid_market_search', name='market_search' )
)
