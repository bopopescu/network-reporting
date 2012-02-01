# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Bootstrap for running a Django app under Google App Engine.

The site-specific code is all in other files: settings.py, urls.py,
models.py, views.py.  And in fact, only 'settings' is referenced here
directly -- everything else is controlled from there.

"""

# Standard Python imports.
import os
import sys
import logging

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

# Google App Engine imports.
from google.appengine.ext.webapp import util

# Import the part of Django that we use here.
import django.core.handlers.wsgi

class MPWSGIHandler(django.core.handlers.wsgi.WSGIHandler):
    def handle_uncaught_exception(self, request, resolver, exc_info):
        """
        Processing for any otherwise uncaught exceptions (those that will
        generate HTTP 500 responses). Can be overridden by subclasses who want
        customised 500 handling.

        Be *very* careful when overriding this because the error could be
        caused by anything, so assuming something like the database is always
        available would be an error.
        """
        from django.conf import settings
        from django.core.mail import mail_admins

        if settings.DEBUG_PROPAGATE_EXCEPTIONS:
            raise

        if settings.DEBUG:
            from django.views import debug
            return debug.technical_500_response(request, *exc_info)

        # When DEBUG is False, send an error message to the admins.
        subject = 'Error (%s IP): %s' % ((request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), request.path)
        try:
            request_repr = repr(request)
        except:
            request_repr = "Request repr() unavailable"
        message = "%s\n\nUSER: %s\n\n%s" % (self._get_traceback(exc_info), self._get_user_email(request), request_repr)
        mail_admins(subject, message, fail_silently=True)
        # If Http500 handler is not installed, re-raise last exception
        if resolver.urlconf_module is None:
            raise exc_info[1], None, exc_info[2]
        # Return an HttpResponse that displays a friendly error message.
        callback, param_dict = resolver.resolve500()
        return callback(request, **param_dict)

    def _get_user_email(self, request):
        return request.user.email if request.user.is_authenticated() else 'Anonymous'

def main():
    # Create a Django application for WSGI.
    application = MPWSGIHandler()
   
    # Run the WSGI CGI handler with that application.
    util.run_wsgi_app(application)
   
if __name__ == '__main__':
    main()
