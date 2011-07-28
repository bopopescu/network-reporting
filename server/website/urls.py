# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from common.constants import (  MARKET_SEARCH_KEY,
                                )

urlpatterns = patterns('website.views',
  url(r'^welcome$', 'website_welcome', name='website_welcome'),
  url(r'^$', 'website_root', name='website_root'),
  url(r'^android_market_search/(?P<qs>.*?)/$', 'droid_market_search', name='market_search')
)
