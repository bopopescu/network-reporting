""" 
Rename this from appengine_config_DEBUG_ONLY.py to appengine_config.py
and uncomment appstats:on in app.yaml
IMPORTANT: When turning back off, remember to delete appengine_config.pyc
"""

from appengine_django import LoadDjango
LoadDjango()
import os
from django.conf import settings

import asdf
asdf.put()


os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
settings._target = None

def webapp_add_wsgi_middleware(app):
    """sdf"""
    print a
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
