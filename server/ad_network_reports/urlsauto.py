# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

rootpatterns = patterns('', (r'^ad_network_reports/', include(
        'ad_network_reports.urls')),)
