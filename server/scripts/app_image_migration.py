import os, sys
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/google")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django_1_2")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append('/'.join(os.getcwd().split("/")[:-1]))
sys.path.append('.')


from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.api import users, images

import urllib2

def auth_func():
    return "olp@mopub.com", "N47935N47935"


from google.appengine.api import files

from publisher.models import App

from common.utils.helpers import chunks

CHUNK_SIZE = 200

  

def main():
    app_id = 'mopub-inc'
    host = '38.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

    apps = App.all().fetch(CHUNK_SIZE)
    new_apps = apps
    print 'total apps:', len(apps)
    while new_apps:
        new_apps = App.all().filter('__key__ >', apps[-1].key()).fetch(CHUNK_SIZE)
        apps += new_apps
        print 'total apps:', len(apps)

    print 'total apps:', len(apps) 
    
    num_apps = len(apps)
    
    apps_to_update = []
    cnt = 0
    for app in apps:
        cnt += 1
        
        # if no icon or migration already happened
        if not app.icon or app.icon_blob: 
            print cnt, 'of', num_apps, 'ALREADY MIGRATED'
            continue
        url = 'http://38-risky.mopub-inc.appspot.com/admin/migrate_image/?app_key=%s' % app.key()
        print cnt, 'of', num_apps, 'url:', url
        try:
            response = urllib2.urlopen(url)
            response.read()
        except:
            print 'FAIL'
        
        # Create the file
        # file_name = files.blobstore.create(mime_type='image/png')
        # 
        # print file_name
        # 
        # # Open the file and write to it
        # with files.open(file_name, 'a') as f:
        #     f.write(app.icon)
        # 
        # # Finalize the file. Do this before attempting to read it.
        # files.finalize(file_name)
        # 
        # # Get the file's blob key
        # blob_key = files.blobstore.get_blob_key(file_name)
        # 
        # # Do not delete image yet
        # # app.icon = None 
        # app.icon_blob = blob_key
        # apps_to_update.append(app)
        
    # write the apps in chunks
    # page = 0
    # for sub_apps in chunks(apps_to_update, CHUNK_SIZE):
    #     page += 1
    #     print 'page', page
    #     db.put(sub_apps)
    
if __name__ == '__main__':
    main()