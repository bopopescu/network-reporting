# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('networks.views',
        url(r'^$',
            'networks',
            name='networks'),

        url(r'^edit/(?P<network>[-\w\.]+)/$',
            'edit_network',
            name='edit_network'),

        url(r'^details/(?P<network>[-\w\.]+)/$',
            'network_details',
            name='network_details'),
        )
