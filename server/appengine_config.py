from appengine_django import LoadDjango
LoadDjango()
import os
from django.conf import settings

""" Rename this from appengine_config_DEBUG_ONLY.py to appengine_config.py
and uncomment appstats:on in app.yaml
IMPORTANT: When turning back off, remember to delete appengine_config.pyc
"""

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# Force Django to reload its settings.
settings._target = None

def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    # app = recording.appstats_wsgi_middleware(app)
    return app
