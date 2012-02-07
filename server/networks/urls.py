# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('networks.views',
        url(r'^$',
            'networks',
            name='networks'),
        )
