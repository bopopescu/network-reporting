# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('bizops.views',
  url(r'^$','dashboard',name='bizops_dashboard'),
)
