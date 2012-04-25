import datetime
import os
import random
import sys
import uuid

from itertools import chain
from optparse import OptionParser


# GAE SDK paths for Mac OS
sys.path.append(os.getcwd()+'/../')
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django_1_2")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")


# GAE SDK paths for ubuntu EC2
sys.path.append('/home/ubuntu/mopub/server')
sys.path.append('/home/ubuntu/mopub/server/reporting')
sys.path.append('/home/ubuntu/google_appengine')
sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
sys.path.append('/home/ubuntu/google_appengine/lib/webob')
sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()



from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

from account.models import Account
from advertiser.models import Campaign, AdGroup, Creative
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager, CreativeQueryManager
from publisher.models import App, Site
from publisher.query_managers import AdUnitQueryManager, AppQueryManager
from reporting.models import StatsModel

LIMIT = 100
START_DATE = datetime.date(2011, 9, 27)
END_DATE = datetime.date(2011, 9, 28)

APP_ID = 'mopub-inc'
HOST = '38-aws.latest.mopub-inc.appspot.com'

def auth_func():
  return 'olp@mopub.com', 'N47935N47935'


def main():
    parser = OptionParser()
    parser.add_option('-a', '--account_id', dest='account_id')
    parser.add_option('-s', '--start_date (YYMMDD)', dest='start_date')
    parser.add_option('-e', '--end_date (YYMMDD)', dest='end_date')
    parser.add_option('-g', '--hour_granularity', action='store_true', dest='hour_granularity', default=False)

    (options, args) = parser.parse_args()
        
    if not options.account_id:
        sys.exit('\nERROR: account_id must be specified\n')
            
    if not options.start_date:
        sys.exit('\nERROR: start_date must be specified in format YYMMDD\n')
    
    print 'patching realtime data for account %s%s in date range:' % (options.account_id, ', with hour granularity,' if options.hour_granularity else '')
        
    # parse start date
    start_year = int('20'+options.start_date[:2])
    start_month = int(options.start_date[2:4])
    start_day = int(options.start_date[-2:])
    print 'start date: %i-%i-%i' % (start_year, start_month, start_day)
    
    # parse end date
    if options.end_date:
        end_year = int('20'+options.end_date[:2])
        end_month = int(options.end_date[2:4])
        end_day = int(options.end_date[-2:])
    else:
        end_year, end_month, end_day = start_year, start_month, start_day
    print 'end date: %i-%i-%i' % (end_year, end_month, end_day)

    
    # connect to GAE datastore
    remote_api_stub.ConfigureRemoteDatastore(APP_ID, '/remote_api', auth_func, HOST)
    
    times = []
    start_dt = datetime.datetime(start_year, start_month, start_day)
    end_dt = datetime.datetime(end_year, end_month, end_day)

    if end_dt < start_dt:
        sys.exit('\nERROR: end_date is earlier than start_date\n')
    

    dt = start_dt
    while dt <= end_dt:
        date = dt.date()
        times.append(date)
        if options.hour_granularity:
            for hour in xrange(24):
                times.append(datetime.datetime(date.year, date.month, date.day, hour))
        dt += datetime.timedelta(1)    
            
    
    # accounts = Account.all().fetch(1000)
    # accounts = accounts[:1]
    accounts = [Account.get(options.account_id)]
    
    for account in accounts:
        if account.user:
            print 'Account:', account.user.email()
        
        
        apps = AppQueryManager.get_apps(account=account, limit=1000)
        adunits = AdUnitQueryManager.get_adunits(account=account, limit=1000)
        campaigns = CampaignQueryManager.get_campaigns(account=account, limit=1000)
        adgroups = AdGroupQueryManager.get_adgroups(account=account, limit=1000)
        creatives = CreativeQueryManager.get_creatives(account=account, limit=1000)
        print 'Apps: %s' % len(apps)
        print 'AdUnits: %s' % len(adunits)
        print 'Campaigns: %s' % len(campaigns)
        print 'AdGroups: %s' % len(adgroups)
        print 'Creatives: %s' % len(creatives)
        
        
        realtime_keys = []
        offline_keys = []
        for advertiser in chain(campaigns, adgroups, creatives, [None]):
            for publisher in chain(apps, adunits, [None]):
                for t in times:
                    if isinstance(t,datetime.datetime):
                        key = StatsModel.get_key(publisher=publisher.key() if publisher else None,
                                                advertiser=advertiser.key() if advertiser else None,
                                                date_hour=t)                    
                    else:
                        key = StatsModel.get_key(publisher=publisher.key() if publisher else None,
                                                advertiser=advertiser.key() if advertiser else None,
                                                date=t)    
                    parent_key = StatsModel.get_key(account=account.key(), publisher=None, advertiser=None)
                    realtime_full_key = db.Key.from_path(key.kind(), key.name(), parent=parent_key)
                    parent_key = StatsModel.get_key(account=account.key(), publisher=None, advertiser=None, offline=True)
                    offline_full_key = db.Key.from_path(key.kind(), key.name(), parent=parent_key)
                    realtime_keys.append(realtime_full_key)
                    offline_keys.append(offline_full_key)

        # print realtime_keys, offline_keys
        page = 1
        print '%i realtime keys' % len(realtime_keys)        
        print '%i offline keys' % len(offline_keys)
        print
        print
        
        while realtime_keys and offline_keys:
            print 'PAGE', page
            # realtime_stats = StatsModel.get(realtime_keys[:LIMIT])
            to_put = []
            offline_stats = StatsModel.get(offline_keys[:LIMIT])
            # print 'getting %i offline stats' % len(offline_stats)

            cnt = 0
            for realtime_key, offline, offline_key in zip(realtime_keys[:LIMIT], offline_stats, offline_keys[:LIMIT]):
                cnt += 1
                if not offline: 
                    # print 'cant find %s||%s' %(offline_key.parent().name(), offline_key.name())
                    # print 'key: %s' % offline_key
                    continue

                properties = offline.properties()
                attrs = dict([(k,getattr(offline,'_'+k)) for k in properties])  

                dynamic_properties = offline.dynamic_properties()
                attrs.update(dict([(k,getattr(offline,k)) for k in dynamic_properties]))

                realtime = StatsModel(key=realtime_key, **attrs)
                to_put.append(realtime)
            
            if len(to_put) > 0:
                print 'putting %s offline stats' % len(to_put)
                db.put(to_put)
            
            # next page
            page += 1
            realtime_keys = realtime_keys[LIMIT:]
            offline_keys = offline_keys[LIMIT:]
            


if __name__ == '__main__':
    main()
