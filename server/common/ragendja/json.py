# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import Promise

import logging

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return super(LazyEncoder, self).default(obj)

class JSONResponse(HttpResponse):
    def __init__(self, pyobj, **kwargs):
        dump = simplejson.dumps(pyobj, cls=LazyEncoder)
        jsonp_callback = kwargs.get('callback', None)
        
        if jsonp_callback:
            dump = jsonp_callback + '(' + dump + '); '

        if kwargs.has_key('callback'):
            del kwargs['callback']
            
        super(JSONResponse, self).__init__(dump,
            content_type='application/json; charset=%s' % settings.DEFAULT_CHARSET,
                                           **kwargs)
