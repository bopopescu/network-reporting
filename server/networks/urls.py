# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('networks.views',
        url(r'^$',
            'networks',
            name='networks'),

        url(r'^create/(?P<network>[-\w\.]+)$',
            'edit_network',
            name='edit_network'),

        url(r'^edit/(?P<campaign_key>[-\w\.]+)$',
            'edit_network',
            name='edit_network'),

        url(r'^details/(?P<campaign_key>[-\w\.]+)$',
            'network_details',
            name='network_details'),

        url(r'^pause$',
            'pause_network',
            name='pause_network'),

        url(r'^delete$',
            'delete_network',
            name='delete_network'),

        url(r'^export$',
            'network_exporter',
            name='network_exporter'),
        )

