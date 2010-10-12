from appengine_django import LoadDjango
LoadDjango()

import os
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# Force Django to reload its settings.
settings._target = None

from google.appengine.ext.appstats.ui import main

if __name__ == '__main__':
    main()