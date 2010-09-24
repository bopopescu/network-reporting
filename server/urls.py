# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from common.ragendja.urlsauto import urlpatterns
from common.ragendja.auth.urls import urlpatterns as auth_patterns
from django.views.generic.simple import direct_to_template,redirect_to

handler500 = 'common.ragendja.views.server_error'

urlpatterns = auth_patterns + patterns('',
    # (r'^$', 'django.views.generic.simple.direct_to_template',
    #     {'template': 'main.html'}),
    (r'^', include('website.urls')),
) + urlpatterns
