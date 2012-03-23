import datetime
import random
import uuid

from reporting.models import Pacific_tzinfo

udids = [uuid.uuid4() for i in range(100)]
adunits = ["adunit%s"%i for i in range(2)]
creatives = ["creative%s"%i for i in range(10)]
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


f = open('sample_log.txt','w')

count_dict = {}
def update_count_dict(action,adunit,creative,date_obj,udid,**kwargs):
    if action == "ad":
        action = "req"
        creative = ""
    
    key = "%s:%s:%s"%(adunit,creative,date_obj.strftime("%Y%m%d%H%M"))

    if not key in count_dict:
        count_dict[key] = dict(req=0,imp=0,aclk=0)    
    count_dict[key][action] += 1

for i in range(20):
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
        
    if d["exclude"]:
        continue

    update_count_dict(**d)    
f.close()

f = open('sample_log_counts.txt','w')
for key in count_dict:
    f.write("%s %s\n"%([count_dict[key].get('req',0),count_dict[key].get('imp',0),count_dict[key].get('aclk',0)],key))
f.close()
