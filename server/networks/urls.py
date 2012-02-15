# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('networks.views',
        url(r'^$',
            'networks',
            name='networks'),

        url(r'^add/$',
            'add_network',
            name='add_network'),

        url(r'^details/$',
            'network_details',
            name='network_details'),
        )
