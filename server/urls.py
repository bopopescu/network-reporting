# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from common.ragendja.urlsauto import urlpatterns
from common.ragendja.auth.urls import urlpatterns as auth_patterns
from django.views.generic.simple import direct_to_template,redirect_to

handler500 = 'common.ragendja.views.server_error'
handler404 = 'common.utils.views.not_found_error'

urlpatterns = auth_patterns + patterns('',
    (r'^_ah/warmup$', 'django.views.generic.simple.direct_to_template',
        {'template': 'common/404.html'}),
    # backend warmup
    (r'^_ah/start$', 'django.views.generic.simple.direct_to_template',
        {'template': 'common/404.html'}),
    (r'^', include('website.urls')),
    # Uncomment the following line to put us in maintenance mode.
    #(r'.*', 'django.views.generic.simple.direct_to_template', {'template': 'common/maintenance.html'}),

) + urlpatterns
