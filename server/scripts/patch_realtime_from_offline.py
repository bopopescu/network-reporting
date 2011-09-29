import os
import sys

sys.path.append(os.getcwd()+'/../')
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django_1_2")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")

import datetime
import random
import uuid

from itertools import chain

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

from advertiser.models import Campaign, AdGroup, Creative
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager, CreativeQueryManager
from publisher.models import App, Site
from publisher.query_managers import AdUnitQueryManager, AppQueryManager
from account.models import Account
from reporting.models import StatsModel

LIMIT = 100
DATES = [datetime.date(2011,8,27),datetime.date(2011,04,27)]
START_DATE = datetime.date(2011, 8, 27)
END_DATE = datetime.date(2011, 8, 28)


def main(app_id="mopub-inc",host="38-aws.latest.mopub-inc.appspot.com"):
    def auth_func():
      return "olp@mopub.com", "N47935"

    # connect to google datastore
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)
    
    times = []
    start_dt = datetime.datetime(START_DATE.year, START_DATE.month, START_DATE.day)
    end_dt = datetime.datetime(END_DATE.year, END_DATE.month, END_DATE.day)
    
    dt = start_dt
    while dt <= end_dt:
        date = dt.date()
        times.append(date)
        for hour in xrange(24):
            times.append(datetime.datetime(date.year,date.month,date.day,hour))
        dt += datetime.timedelta(1)    
            
    
    # accounts = Account.all().fetch(1000)
    # accounts = accounts[:1]
    accounts = [Account.get('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY09GeAQw')]
    
    for account in accounts:
        if account.user:
            print "Account",account.user.email()
        
        
        apps = AppQueryManager.get_apps(account=account,limit=1000)
        adunits = AdUnitQueryManager.get_adunits(account=account,limit=1000)
        campaigns = CampaignQueryManager.get_campaigns(account=account,limit=1000)
        adgroups = AdGroupQueryManager.get_adgroups(account=account,limit=1000)
        creatives = CreativeQueryManager.get_creatives(account=account,limit=1000)
        print "Apps: %s"%len(apps)
        print "AdUnits: %s"%len(adunits)
        print "Campaigns: %s"%len(campaigns)
        print "AdGroups: %s"%len(adgroups)
        print "Creatives: %s"%len(creatives)
        
        
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
                    parent_key = StatsModel.get_key(account=account.key(),publisher=None,advertiser=None)
                    realtime_full_key = db.Key.from_path(key.kind(),key.name(),parent=parent_key)
                    parent_key = StatsModel.get_key(account=account.key(),publisher=None,advertiser=None,offline=True)
                    offline_full_key = db.Key.from_path(key.kind(),key.name(),parent=parent_key)
                    realtime_keys.append(realtime_full_key)
                    offline_keys.append(offline_full_key)

        # print realtime_keys, offline_keys
        page = 1
        while realtime_keys and offline_keys:
            print 'PAGE',page
            # realtime_stats = StatsModel.get(realtime_keys[:LIMIT])
            to_put = []
            print 'getting %s offline stats'%len(offline_keys[:LIMIT])
            offline_stats = StatsModel.get(offline_keys[:LIMIT])
            print 'got'
            cnt = 0
            for realtime_key, offline in zip(realtime_keys[:LIMIT],offline_stats):
                cnt += 1
                if not offline: continue

                properties = offline.properties()
                attrs = dict([(k,getattr(offline,'_'+k)) for k in properties])  

                dynamic_properties = offline.dynamic_properties()
                attrs.update(dict([(k,getattr(offline,k)) for k in dynamic_properties]))

                realtime = StatsModel(key=realtime_key,**attrs)
                to_put.append(realtime)
            print 'putting %s offline stats'%len(to_put)
            db.put(to_put)    
            
            # next page
            page += 1
            realtime_keys = realtime_keys[LIMIT:]
            offline_keys = offline_keys[LIMIT:]
            


if __name__ == '__main__':
    main()