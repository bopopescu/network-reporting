import codecs
try:
    import json
except ImportError:
    import simplejson as json
import os
import sys
import traceback

import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

ACCESS_KEY_ID = 'AKIAJKOJXDCZA3VYXP3Q'
SECRET_ACCESS_KEY = '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'


def _upload_progress(complete, total):
    sys.stdout.write('.')
    sys.stdout.flush()


def upload_file_to_S3(local_file_path, s3_bucket, s3_file_path):
    try:
        s3_conn = S3Connection(ACCESS_KEY_ID, SECRET_ACCESS_KEY)
        bucket = s3_conn.get_bucket(s3_bucket)
        s3_file = Key(bucket)
        s3_file.key = s3_file_path

        s3_file.set_contents_from_filename(local_file_path,
                                        cb=_upload_progress,
                                        num_cb=10)
        print '\nuploaded %s to %s' % (local_file_path, 's3://%s%s' % (s3_bucket, s3_file_path))
        return True
    except:
        traceback.print_exc()
        return False


def create_unicode_mapping_file(file_name, mapping_dict, id_header, name_header):
    cur_dir = os.path.dirname(os.path.abspath( __file__ ))

    f = codecs.open(file_name, encoding='utf-8', mode='w')
    for k, v in mapping_dict.iteritems():
        # Hive json serde can't handle null, which is JSON equivalent of Python None; use string instead
        v = v or 'NONE'

        line = json.dumps({id_header: k, name_header: v}, ensure_ascii=False)
        try:
            f.write(line+'\n')
        except:
            print type(line)
            print line
    f.close()

    return os.path.join(cur_dir, file_name)
