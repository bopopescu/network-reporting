import datetime

""" This is eventually where all of the frequency capping logic will live.
    For now, we just have a few helper functions. """

############## HELPER FUNCTIONS ################
def memcache_key_for_date(udid,datetime,db_key):
    return '%s:%s:%s'%(udid,datetime.strftime('%y%m%d'),db_key)

def memcache_key_for_hour(udid,datetime,db_key):
    return '%s:%s:%s'%(udid,datetime.strftime('%y%m%d%H'),db_key)
