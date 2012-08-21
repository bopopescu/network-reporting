from __future__ import with_statement
import sys
import warnings
from django.core.management.base import BaseCommand
from google.appengine.ext.remote_api import remote_api_stub



def auth_func():
  return "testuser","testpassword"

class Command(BaseCommand):
    """ Start up an interactive console backed by your app using remote_api """

    help = 'Generate data using the remote api'

    def run_from_argv(self, argv):
        host = "localhost:8000"
        app_id = "dev~mopub-inc"

        remote_api_stub.ConfigureRemoteDatastore(app_id,
                                                 '/remote_api',
                                                 auth_func,
                                                 host)
        from admin.randomgen import main
        main()

