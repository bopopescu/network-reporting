# TESTING INSTRUCTIONS (After following instructions in setup.py)
# $ python loader.py

# add mopub root to path
import os
import sys
sys.path.append(os.getcwd()+'/../../')

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

import urllib, urllib2

from google.appengine.ext import db
from publisher.models import AdUnit


KEY_NAME_FORMAT = 'adunit_%02d'
URL = 'http://localhost:8000/m/ad?id='

def main():
    for i in xrange(100):
        key = str(db.Key.from_path(AdUnit.kind(),KEY_NAME_FORMAT%i))
        req = urllib2.Request(URL+key)
        response = urllib2.urlopen(req)
        the_page = response.read()
        print key, the_page

if __name__ == '__main__':
    main()
