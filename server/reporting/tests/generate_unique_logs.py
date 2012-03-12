import os
import sys

sys.path.append(os.getcwd()+'/../../')
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django_1_2")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")

import datetime
import random
import uuid

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import App, Site
from account.models import Account
from reporting.models import Pacific_tzinfo
AdUnit = Site


NUM_LOGS = 1000

def main(app_id="mopub-inc",host="38-aws.latest.mopub-inc.appspot.com"):
    def auth_func():
      return "olp@mopub.com", "N47935N47935"
    
    # connect to google datastore
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)


    print "PUTTING OBJECTS"
    user = users.get_current_user()
    account = Account(key_name="account",user=user).put()

    app_obj = App(key_name='app1', name='App',account=account)
    app = app_obj.put()
    app2_obj = App(key_name='app2', name='App2',account=account)
    app2 = app2_obj.put()
    adunit1_obj = AdUnit(key_name='adunit1', app_key=app, account=account)
    adunit1 = adunit1_obj.put()
    adunit2_obj = AdUnit(key_name='adunit2', app_key=app, account=account)
    adunit2 = adunit2_obj.put()
    adunit3_obj = AdUnit(key_name='adunit3', app_key=app2, account=account)
    adunit3 = adunit3_obj.put()

    campaign_obj = Campaign(key_name='campaign', name='campaign',account=account, u=user)
    campaign = campaign_obj.put()
    adgroup_obj = AdGroup(key_name='adgroup', campaign=campaign,account=account)
    adgroup = adgroup_obj.put()
    adgroup2_obj = AdGroup(key_name='adgroup2', campaign=campaign,account=account)
    adgroup2 = adgroup2_obj.put()
    creative1_obj = Creative(key_name='creative1', ad_group=adgroup,account=account)
    creative1 = creative1_obj.put()
    creative2_obj = Creative(key_name='creative2', ad_group=adgroup,account=account)
    creative2 = creative2_obj.put()
    creative3_obj = Creative(key_name='creative3', ad_group=adgroup,account=account)
    creative3 = creative3_obj.put()
    creative4_obj = Creative(key_name='creative4', ad_group=adgroup2,account=account)
    creative4 = creative4_obj.put()
    creative5_obj = Creative(key_name='creative5', ad_group=adgroup2,account=account)
    creative5 = creative5_obj.put()
    creative6_obj = Creative(key_name='creative6', ad_group=adgroup2,account=account)
    creative6 = creative6_obj.put()
    print "DONE PUTTING OBJECTS"
    
    # object and
    # owner lookup
    global obj_dict
    obj_dict = {
        str(creative1): creative1_obj,
        str(creative2): creative2_obj,
        str(creative3): creative3_obj,
        str(creative4): creative4_obj,
        str(creative5): creative5_obj,
        str(creative6): creative6_obj,
        str(adunit1): adunit1_obj,
        str(adunit2): adunit2_obj,
        str(adunit3): adunit3_obj,
    }
    
    
    global udids, adunits, creatives, ips, user_agents, actions, excludes, dates
    
    
    udids = [uuid.uuid4() for i in range(100)]
    adunits = [adunit1,adunit2,adunit3]
    adunits = [str(a) for a in adunits]
    creatives = [creative1,creative2,creative3,creative4,creative5,creative6]
    creatives = [str(c) for c in creatives]
    ips = ["%i.%i.%i.%i"%(random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255)) for i in range(100)]
    user_agents = ["GaiaLite/4.4 (iPhone; U; CPU iPhone OS 4.0.1 like Mac OS X; es_ES),gzip(gfe),gzip(gfe),gzip(gfe)"]
    actions = ["/m/ad","/m/imp","/m/req","/m/aclk"]
    excludes = ["","exclude=iAd"]
    dates = [datetime.datetime(2011,04,02,22,10,tzinfo=Pacific_tzinfo()),
             datetime.datetime(2011,04,02,22,20,tzinfo=Pacific_tzinfo()),
             datetime.datetime(2011,04,02,23,10,tzinfo=Pacific_tzinfo()),
             datetime.datetime(2011,04,03,00,10,tzinfo=Pacific_tzinfo()),
             datetime.datetime(2011,04,03,01,10,tzinfo=Pacific_tzinfo()),]

    # 174.253.18.133 - - [23/Mar/2011:15:57:21 -0700] "GET /m/imp?id=agltb3B1Yi1pbmNyDAsSBFNpdGUY1NsgDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGOj6IAw&udid=577a639187e2ff11 HTTP/1.1" 200 146 "http://ads.mopub.com/" "Mozilla/5.0 (Linux; U; Android 2.2.1; en-us; DROIDX Build/VZW) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1,gzip(gfe),gzip(gfe),gzip(gfe)"
    AD_LOG_FORMAT = '%(ip)s - - [%(date)s] "GET %(action)s?id=%(adunit)s&udid=%(udid)s&%(exclude)s HTTP/1.1" 200 146 "http://ads.mopub.com/" "%(user_agent)s"'
    ALL_LOG_FORMAT = '%(ip)s - - [%(date)s] "GET %(action)s?id=%(adunit)s&cid=%(creative)s&udid=%(udid)s HTTP/1.1" 200 146 "http://ads.mopub.com/" "%(user_agent)s"'

    def pick_random(param):
        # grabs the appropriate param list 
        l = globals()[param+"s"]
        length = len(l)
        index = random.randint(0,length-1)
        return l[index]


    f = open('sample_unique_log.log','w')

    count_dict = {}
    def update_count_dict(action,adunit,creative,date_obj,udid,**kwargs):
        if action == "/m/ad":
            creative = ""

        advs = []
        if creative:    
            creative_obj = obj_dict[creative]
            advs.append(str(creative_obj.key()))

            adgroup_obj = creative_obj.adgroup
            advs.append(str(adgroup_obj.key()))

            campaign_obj = adgroup_obj.campaign
            advs.append(str(campaign_obj.key()))
        advs.append("") # wildcard    

        adunit_obj = obj_dict[adunit]
        account_obj = adunit_obj.account
        account = str(account_obj.key())
        app_obj = adunit_obj.app

        pubs = [adunit]
        pubs.append(app_obj.key())
        pubs.append("") # wildcard
        
        actions = [action,""]

        dates = [date_obj.strftime("%y%m%d%H"),date_obj.strftime("%y%m%d")]

        keys = set()    
        for pub in pubs:
            for adv in advs:
                for date in dates:
                    for action in actions:
                        key = "k:%s:%s:%s:%s:%s"%(action,account,pub,adv,date)
                        keys.add(key)

        for key in keys:            
            if not key in count_dict:
                count_dict[key] = set()
            count_dict[key].add(udid)

    for i in range(NUM_LOGS):
        params = ["ip","date","action","adunit","creative","udid","user_agent","exclude"]
        d = dict()
        for param in params:
            value = pick_random(param)
            if param == "date":
                d.update(date_obj=value)
                value = value.strftime("%d/%b/%Y:%H:%M:%S %z")
            d.update({param:value})
        if d["action"] == "ad":    
            f.write(AD_LOG_FORMAT%d+'\n')
        else:
            f.write(ALL_LOG_FORMAT%d+'\n')    

        if d["exclude"] and d["action"] == "ad":
            continue

        update_count_dict(**d)    
    f.close()

    f = open('sample_unique_log_counts.log','w')
    keys = count_dict.keys()
    keys.sort()
    for key in keys:
        f.write("%s %s\n"%(key,len(count_dict[key])))
    f.close()


if __name__ == '__main__':
    main()  
