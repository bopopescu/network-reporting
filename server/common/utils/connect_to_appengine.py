from google.appengine.ext.remote_api import remote_api_stub
APP_ID = 'mopub-inc'
HOST = '38.latest.mopub-inc.appspot.com'
REMOTE_API = '/remote_api'

EMAIL = 'olp@mopub.com'
PASSWORD = 'N47935N47935'

def setup_remote_api():
    remote_api_stub.ConfigureRemoteDatastore(APP_ID, REMOTE_API, auth_func,
            HOST)

def auth_func():
    return EMAIL, PASSWORD

