# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

rootpatterns = patterns('', (r'^ad_network_reports/', include('network_scraping.urls')),)