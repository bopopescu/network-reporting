import datetime
import os
import sys

sys.path.append(os.environ['PWD'])

from google.appengine.ext import db
from nose.tools import eq_

from account.models import Account
from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import App, AdUnit
from reporting.models import StatsModel


def prepend_list(e, li):
    li.insert(0, e)
    return li


def add_lists(list_of_lists):
    result = list_of_lists[0]
    for li in list_of_lists[1:]:
        result = map(sum, zip(result, li))
    return result


def clear_datastore():
    db.delete(Account.all())
    db.delete(AdUnit.all())
    db.delete(App.all())
    db.delete(Creative.all())
    db.delete(AdGroup.all())
    db.delete(Campaign.all())
    db.delete(StatsModel.all())


def debug_key_name(key_name, id_dict):
    return ':'.join([id_dict.get(id, id) for id in key_name.split(':')])


def debug_helper(readable_key_name, expected_counts, actual_counts):
    if expected_counts != actual_counts:
        print
        print readable_key_name
        print 'expected:', expected_counts
        print 'actual:', actual_counts


def dict_eq(dict1, dict2, exclude=[]):
    dict1_keys = set(dict1.keys()) - set(exclude)
    dict2_keys = set(dict2.keys()) - set(exclude)

    msg = "passed dictionary keys did not match: %s %s" % (
            dict1_keys - dict2_keys, dict2_keys - dict1_keys)
    eq_(dict1_keys, dict2_keys, msg)

    for key in dict1_keys:
        if isinstance(dict1[key], db.Model):
            model_key_eq(dict1[key], dict2[key])
        else:
            eq_(dict1[key], dict2[key])


def model_key_eq(model1, model2):
    eq_(model1.key(), model2.key())


def model_to_dict(model, exclude=[]):
    model_dict = {}

    for key, prop in model.properties().iteritems():
        if key in exclude:
            continue
        model_dict[key] = getattr(model, key)

    return model_dict

def time_almost_eq(time1, time2, delta):
    pass
