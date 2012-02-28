#publisher = site(adunit), app
#advertiser = creative, adgroup, campaingn

import os, sys
import pickle
import traceback
sys.path.append(os.getcwd()+'/../')
sys.path.append('.')

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()
from dateutil.relativedelta import relativedelta
from datetime import datetime
from publisher.models import Site as Adunit, App
from reporting.models import StatsModel
from datetime import date

from google.appengine.ext.db import Timeout

LIMIT = 1000

def auth_func():
    return "olp@mopub.com", "N47935N47935"

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub

    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

def gen_range(start, end):
    while start <= end:
        yield start
        start = start + relativedelta(days=+1)

def process_stats(stats, cur_date_stats):
    for stat in stats:
        cur_date_stats.append(stat)

def pickle_to_file(pkl_obj, pkl_file):
    print '\npickling to %s ...' % (pkl_file)
    with open(pkl_file, 'w') as pf:
        pickle.dump(pkl_obj, pf)
    print '%i entries pickled' % (len(pkl_obj))

def main():
    setup_remote_api()
    
    start_date = date(2011,11,1)
    end_date = date(2011,12,7)
    for cur_date in gen_range(start_date, end_date):
        # process all stats
        cur_date_stats = []
        print 'Stats...'
        try:
            total = 0
            stats = StatsModel.all().filter('date =', cur_date).fetch(LIMIT)
            while len(stats) == LIMIT:
                process_stats(stats, cur_date_stats)
                total += LIMIT
                print 'fetched %i StatsModels so far' % (total)
                last_key = stats[-1].key()
                stats = StatsModel.all().filter('date =', cur_date).\
                    filter('__key__ >', last_key).fetch(LIMIT)
            # process last batch < LIMIT
            process_stats(stats, cur_date_stats)
            total += len(stats)
            print 'fetched %i StatsModel total' % (total)
            pickle_to_file(cur_date_stats, 'stats_models' + str(cur_date) + '.pkl')
        except:
            traceback.print_exc()

if __name__ == '__main__':
    main()
