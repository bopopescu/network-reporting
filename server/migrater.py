from __future__ import with_statement

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

import urllib2
from common.utils import helpers
from google.appengine.api import images, files
from mapreduce import operation as op
# from reporting.models import StatsModel, MPStatsModel
from publisher.models import App
def mapper(s):
    # change entity
    props = {}
    for k in StatsModel.properties():
        props[k] = getattr(s,'_%s'%k) # gets underlying data w/ no derefernce

    for k in s.dynamic_properties():
        props[k] = getattr(s,k)

    account = props.get('account',None)
    offline = props.get('offline',False)
    parent_key = None
    parent = s.parent()

    if not account and parent:
        # parent = StatsModel.get(parent.key())
        # if parent:
        account = parent._account

    if account and parent:
        props.update(account=account)
        parent_key = MPStatsModel.get_key(account=account,
                                          offline=offline,
                                          publisher=None,advertiser=None)
    new_stat = MPStatsModel(parent=parent_key,**props)
    yield op.db.Put(new_stat)
    # or yield op.db.Delete(entity)

def deleter(entity):
    yield op.db.Delete(entity)

def blober(entity):
    image_blob = None
    _attribute = None
    if hasattr(entity, 'icon_blob'):
        image_blob = entity.icon_blob if entity.icon_blob else None
        attribute = 'icon_blob'
        entity.icon = None
    elif hasattr(entity, 'image_blob'):
        image_blob = entity.image_blob if entity.image_blob else None
        attribute = 'image_blob'
    if image_blob_key:
        try:
            helpers.helpers.get_url_for_blob(image_blob)
        # if we get an invalidblobkeyerror that means the image still needs to be transfered
        except InvalidBlobKeyError:
            image = urllib2.urlopen('http://38-aws.mopub-inc.appspot.com/files/serve/%s' % image_blob.key())
            setattr(entity, attribute, store_icon(image.read()))
            yield op.db.Put(entity)

def store_icon(icon):
    # add the icon it to the blob store
    fname = files.blobstore.create(mime_type='image/png')
    with files.open(fname, 'a') as f:
        f.write(icon)
    files.finalize(fname)
    return files.blobstore.get_blob_key(fname)

def blob_urler(obj):
    image_blob = None
    if hasattr(obj, 'icon_blob'):
        image_blob = obj.icon_blob if obj.icon_blob else None
    elif hasattr(obj, 'image_blob'):
        image_blob = obj.image_blob if obj.image_blob else None

    if image_blob and not obj.image_serve_url:
        obj.image_serve_url = helpers.get_url_for_blob(image_blob, ssl=False)
        yield op.db.Put(obj)


def creative_pauser(creative):
    if getattr(creative, 'image_blob', None):
        creative.was_active = creative.active
        creative.active = False
        yield op.db.Put(creative)

def creative_activater(creative):
    if getattr(creative, 'image_blob', None):
        creative.active = creative.was_active
        yield op.db.Put(creative)


def network_configer(obj):
    network_config = getattr(obj, 'network_config', None)
    if network_config:
        network_config.account = obj._account  # key only
        yield op.db.Put(network_config)
