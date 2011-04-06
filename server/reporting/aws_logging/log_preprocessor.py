import sys
import time
import traceback

from optparse import OptionParser

sys.path.append("/home/ubuntu/mopub/server")
sys.path.append("/home/ubuntu/mopub/server/reporting")
sys.path.append("/home/ubuntu/google_appengine")
sys.path.append("/home/ubuntu/google_appengine/lib/django")
sys.path.append("/home/ubuntu/google_appengine/lib/webob")
sys.path.append("/home/ubuntu/google_appengine/lib/yaml/lib")
sys.path.append("/home/ubuntu/google_appengine/lib/fancy_urllib")

# from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

import utils


def preprocess_logs(input_file):
    output_file = input_file + ".pp"  # for preprocessed
    with open(input_file, 'r') as in_stream:
        with open(output_file, 'w') as out_stream:
            for line in in_stream:
                pp_line = utils.preprocess_logline(line)
                if pp_line:
                    out_stream.write(pp_line)
            
       
def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', utils.auth_func, host)
    
    preprocess_logs(options.input_file)

    elapsed = time.time() - start
    print 'preprocessing logs took %i minutes and %i seconds' % (elapsed/60, elapsed%60)
    print 'preprocessed logs written to %s.pp'%options.input_file
    

if __name__ == '__main__':
    main()
