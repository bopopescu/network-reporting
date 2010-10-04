import logging, os, sys
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

from google.appengine.dist import use_library
use_library("django", "1.1") # or use_library("django", "1.0") if you're using 1.0

from django.conf import settings
settings._target = None

from google.appengine.ext.appstats.ui import main

if __name__ == '__main__':
    main()