from __future__ import with_statement
import cPickle as pickle
import logging

from google.appengine.api import files
from google.appengine.ext import db, blobstore
from StringIO import StringIO
import urllib2

def upload_file(fd):
    from poster.encode import multipart_encode
    from poster.streaminghttp import register_openers
    BACKEND = 'stats-updater'
    APP = 'mopub-inc'
    HOST = 'http://%s.%s.appspot.com' % (BACKEND, APP)
    URL_HANDLER_PATH = '/offline/get_upload_url'

    register_openers()
    datagen, headers = multipart_encode({'file' : fd})

    upload_url_req = urllib2.Request(HOST + URL_HANDLER_PATH)
    upload_url = urllib2.urlopen(upload_url_req).read()

    file_upload_req = urllib2.Request(upload_url, datagen, headers)
    blob_key = urllib2.urlopen(file_upload_req).read()
    return blob_key


class DictProperty(db.Property):
    data_type = dict

    def get_value_for_datastore(self, model_instance):
        value = super(DictProperty, self).get_value_for_datastore(model_instance)
        data = pickle.dumps(value)
        try:
            file_name = files.blobstore.create(mime_type='application/octet-stream')
            with files.open(file_name, 'a') as f:
                f.write(data)
            files.finalize(file_name)
            blob_key = files.blobstore.get_blob_key(file_name)
            return blob_key
        except:
            # This should only be run by AWS, only one proc @ a time, so only
            # one person will be using this file @ a time
            with open('/tmp/temp_report.tmp', 'w') as fd:
                fd.write(data)
            with open('/tmp/temp_report.tmp', 'r') as fd:
                blob_key = upload_file(fd)
            return blobstore.BlobKey(blob_key)


    def make_value_from_datastore(self, value):
        if value is None:
            return dict()
        if isinstance(value, blobstore.BlobKey):
            blob_info = blobstore.BlobInfo.get(value)
            reader = blob_info.open()
            data = reader.read()
            ret_data = pickle.loads(data)
            return ret_data
            #return pickle.loads(reader.read())
        else:
            return pickle.loads(value)

    def default_value(self):
        if self.default is None:
            return dict()
        else:
            return super(DictProperty, self).default_value().copy()

    def validate(self, value):
        if not isinstance(value, dict):
            raise db.BadValueError('Property %s needs to be convertible to a dict instance (%s) of class dict' % (self.name, value))
        return super(DictProperty, self).validate(value)

    def empty(self, value):
        return value is None
