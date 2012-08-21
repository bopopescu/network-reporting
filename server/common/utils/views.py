from django.http import HttpResponseNotFound
from common.ragendja.template import render_to_string

def not_found_error(request, *args, **kwargs):
	if request.META['HTTP_HOST'] == "ads.mopub.com":
	    return HttpResponseNotFound('404: Not Found')
	else:
	    return HttpResponseNotFound(render_to_string(request, 'common/404.html'))
