from django.conf import settings
from django.http import HttpResponseServerError
from common.ragendja.template import render_to_string

def server_error(request, *args, **kwargs):
    debugkey = request.REQUEST.get('debugkey')
    if debugkey and debugkey == getattr(settings, 'DEBUGKEY', None):
        import sys,logging
        from django.views import debug
        return debug.technical_500_response(request, *sys.exc_info())
    return HttpResponseServerError(render_to_string(request, 'common/500.html'))

def maintenance(request, *args, **kwargs):
    return HttpResponseServerError(render_to_string(request,
        'common/maintenance.html'))
