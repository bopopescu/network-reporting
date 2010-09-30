# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

rootpatterns = patterns('',
    (r'^admin/', include('admin.urls')),
)
