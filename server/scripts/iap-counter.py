import os
import sys


# Mac OS paths
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")


# Ubuntu EC2 paths
sys.path.append('/home/ubuntu/mopub/server')
sys.path.append('/home/ubuntu/mopub/server/reporting')
sys.path.append('/home/ubuntu/google_appengine')
sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
sys.path.append('/home/ubuntu/google_appengine/lib/webob')
sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')


from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

sys.path.append(os.path.dirname(os.getcwd()))   # assuming this script is run within its own dir, adds server root dir to the path
from userstore.models import InAppPurchaseEvent


LIMIT = 300


def auth_func():
    return "olp@mopub.com", "N47935N47935"


def main():
    total_count = 0

    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

    mobile_users = {}

    keys = InAppPurchaseEvent.all(keys_only=True).fetch(LIMIT)
    while len(keys) == LIMIT:
        total_count += LIMIT
        print total_count,

        for key in keys:
            mobile_user_key = key.parent()
            mobile_users[str(mobile_user_key)] = mobile_users.get(str(mobile_user_key), 0) + 1

        last_key = keys[-1]
        keys = InAppPurchaseEvent.all(keys_only=True).filter('__key__ >', last_key).fetch(LIMIT)

    # process last batch under LIMIT
    total_count += len(keys)
    for key in keys:
        mobile_user_key = key.parent()
        mobile_users[str(mobile_user_key)] = mobile_users.get(str(mobile_user_key), 0) + 1


    print
    print
    print 'total IAP events:', total_count
    print 'total users:', len(mobile_users)
    print

    freq_dict = {}
    for user, count in mobile_users.iteritems():
        freq_dict[count] = freq_dict.get(count, 0) + 1


    for bucket, freq in freq_dict.iteritems():
        print bucket, freq




if __name__ == '__main__':
    main()

