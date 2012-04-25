import os
import sys

sys.path.append(os.environ['PWD'])

from google.appengine.ext import db

from advertiser.models import *
from publisher.models import *
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
