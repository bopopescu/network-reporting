""" This is eventually where all of the frequency capping logic will live.
    For now, we just have a few helper functions. """

from google.appengine.ext import db

############## HELPER FUNCTIONS ################
def memcache_key_for_date(udid, datetime, db_key):
    return '%s:%s:%s' % (udid, datetime.strftime('%d'), db_key)

def memcache_key_for_hour(udid, datetime, db_key):
    return '%s:%s:%s' % (udid, datetime.strftime('%H'), db_key)

def id_or_key_name(db_key):
    """
    Returns the id or key name of the inputted db_key
    """
    if not isinstance(db_key, db.Key):
        db_key = db.Key(db_key)
    return db_key.id_or_name()    