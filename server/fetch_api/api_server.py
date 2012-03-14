#!/usr/bin/env python
from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from fetch_api.auc_fetch_handler import AUCFetchHandler


def main():
    app = webapp.WSGIApplication([
            ('/fetch_api/adunit/(?P<adunit_key>[-\w\.]+)/fetch_context', AUCFetchHandler),
            ])
    run_wsgi_app(app)

if __name__ == '__main__':
    main()