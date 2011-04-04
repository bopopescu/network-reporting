import datetime
import random
import uuid

from google.appengine.api import users
from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import App, Site
from account.models import Account
from reporting.models import Pacific_tzinfo
AdUnit = Site


user = users.User(email="test@example.com")
account = Account(key_name="account",user=user).put()

app = App(key_name='app1', name='App',account=account).put()
app2 = App(key_name='app2', name='App2',account=account).put()
adunit1 = AdUnit(key_name='adunit1', app_key=app, account=account).put()
adunit2 = AdUnit(key_name='adunit2', app_key=app, account=account).put()
adunit3 = AdUnit(key_name='adunit3', app_key=app2, account=account).put()

campaign = Campaign(key_name='campaign', name='campaign',account=account, u=user).put()
adgroup = AdGroup(key_name='adgroup', campaign=campaign,account=account).put()
adgroup2 = AdGroup(key_name='adgroup2', campaign=campaign,account=account).put()
creative1 = Creative(key_name='creative1', ad_group=adgroup,account=account).put()
creative2 = Creative(key_name='creative2', ad_group=adgroup,account=account).put()
creative3 = Creative(key_name='creative1', ad_group=adgroup,account=account).put()
creative4 = Creative(key_name='creative2', ad_group=adgroup2,account=account).put()
creative5 = Creative(key_name='creative1', ad_group=adgroup2,account=account).put()
creative6 = Creative(key_name='creative2', ad_group=adgroup2,account=account).put()


udids = [uuid.uuid4() for i in range(100)]
adunits = [adunit1,adunit2,adunit3]
adunits = [str(a) for a in adunits]
creatives = [creative1,creative2,creative3,creative4,creative5,creative6]
creatives = [str(c) for c in creatives]
ips = ["%i.%i.%i.%i"%(random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255)) for i in range(100)]
user_agents = ["GaiaLite/4.4 (iPhone; U; CPU iPhone OS 4.0.1 like Mac OS X; es_ES),gzip(gfe),gzip(gfe),gzip(gfe)"]
actions = ["ad","imp","req","aclk"]
excludes = ["","exclude=iAd"]
dates = [datetime.datetime(2011,04,02,22,10,tzinfo=Pacific_tzinfo()),
         datetime.datetime(2011,04,02,22,20,tzinfo=Pacific_tzinfo()),
         datetime.datetime(2011,04,02,23,10,tzinfo=Pacific_tzinfo()),
         datetime.datetime(2011,04,03,00,10,tzinfo=Pacific_tzinfo()),
         datetime.datetime(2011,04,03,01,10,tzinfo=Pacific_tzinfo()),]

# 174.253.18.133 - - [23/Mar/2011:15:57:21 -0700] "GET /m/imp?id=agltb3B1Yi1pbmNyDAsSBFNpdGUY1NsgDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGOj6IAw&udid=577a639187e2ff11 HTTP/1.1" 200 146 "http://ads.mopub.com/" "Mozilla/5.0 (Linux; U; Android 2.2.1; en-us; DROIDX Build/VZW) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1,gzip(gfe),gzip(gfe),gzip(gfe)"
AD_LOG_FORMAT = '%(ip)s - - [%(date)s] "GET /m/%(action)s?id=%(adunit)s&udid=%(udid)s&%(exclude)s HTTP/1.1" 200 146 "http://ads.mopub.com/" "%(user_agent)s"'
ALL_LOG_FORMAT = '%(ip)s - - [%(date)s] "GET /m/%(action)s?id=%(adunit)s&cid=%(creative)s&udid=%(udid)s HTTP/1.1" 200 146 "http://ads.mopub.com/" "%(user_agent)s"'

def pick_random(param):
    # grabs the appropriate param list 
    l = globals()[param+"s"]
    length = len(l)
    index = random.randint(0,length-1)
    return l[index]


f = open('sample_unique_log.txt','w')

count_dict = {}
def update_count_dict(action,adunit,creative,date_obj,udid,**kwargs):
    if action == "ad":
        action = "req"
        creative = ""
    
    advs = []
    if creative:    
        creative_obj = Creative.get(creative)
        advs.append(str(creative_obj.key()))

        adgroup_obj = creative_obj.adgroup
        advs.append(str(adgroup_obj.key()))

        campaign_obj = adgroup_obj.campaign
        advs.append(str(campaign_obj.key()))
    advs.append("") # wildcard    

    adunit_obj = AdUnit.get(adunit)    
    account_obj = adunit_obj.account
    account = str(account_obj.key())
    app_obj = adunit_obj.app
    
    pubs = [adunit]
    pubs.append(app_obj.key())
    pubs.append("") # wildcard
    
    dates = [date_obj.strftime("%Y%m%d%H"),date_obj.strftime("%Y%m%d")]
    
    keys = []    
    for pub in pubs:
        for adv in advs:
            for date in dates:
                key = "k:%s:%s:%s:%s:%s"%(action,account,pub,adv,date)
                keys.append(key)
    for key in keys:            
        if not key in count_dict:
            count_dict[key] = set()
        count_dict[key].add(udid)

for i in range(1000):
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

f = open('sample_unique_log_counts.txt','w')
for key in count_dict:
    f.write("%s %s\n"%(key,len(count_dict[key])))
f.close()