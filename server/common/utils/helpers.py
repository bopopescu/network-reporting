import re, logging
import reporting.models as reporting_models

# matches sequence: space, 2 char, - or _, 2 char, 0 or more ;, followed by char that's not a char, number, - or _
COUNTRY_PAT = re.compile(r' [a-zA-Z][a-zA-Z][-_](?P<ccode>[a-zA-Z][a-zA-Z]);*[^a-zA-Z0-9-_]')


def get_country_code(user_agent):
    m = COUNTRY_PAT.search(user_agent)
    if m:
        country_code = m.group('ccode')
        return country_code.upper()
    return reporting_models.DEFAULT_COUNTRY
    
def get_user_agent(request):
    return request.get('ua') or request.headers['User-Agent']    
    
def get_ip(request):
    return request.get('ip') or request.remote_addr

# dte:pub:adv:CC:BN:MN:OS:OSVER
STAT_KEY = "%s:%s:%s:%s:%s:%s:%s:%s"

def build_key(stat):
    #doesn't really matter since this will be consistent among all these 
    #stat objs.  
    dte = stat.date or stat.date_hour
    pub = str(stat.publisher.key()) if stat.publisher else '*'
    adv = str(stat.advertiser.key()) if stat.advertiser else '*'
    cc = stat.country or '*'
    bn = stat.brand_name or '*'
    mn = stat.marketing_name or '*'
    os = stat.device_os or '*'
    osver = stat.device_os_version or '*'
    return STAT_KEY % (dte, pub, adv, cc, bn, mn, os, osver)

def build_keys(stat):
    dte = stat.date or stat.date_hour
    if stat.publisher:
        pubs = [str(stat.publisher.key()), '*']
    else:
        pubs = ['*']
    if stat.advertiser:
        advs = [str(stat.advertiser.key()), '*']
    else:
        advs = ['*']
    if stat.country:
        ccs = [stat.country, '*']
    else:
        ccs = ['*']
    if stat.brand_name:
        bns = [stat.brand_name, '*']
    else:
        bns = ['*']
    if stat.marketing_name:
        mns = [stat.marketing_name, '*']
    else:
        mns = ['*']
    if stat.device_os:
        oss = [stat.device_os, '*']
    else:
        oss = ['*']
    if stat.device_os_version:
        osvers = [stat.device_os_version, '*']
    else:
        osvers = ['*']
    keys = []
    for pub in pubs:
        for adv in advs:
            for cc in ccs:
                for bn in bns:
                    for mn in mns:
                        for os in oss:
                            for osver in osvers:
                                keys.append(STAT_KEY % (dte, pub, adv, cc, bn, mn, os, osver))
    return keys

def been_seen(stat, seen):
    keys = build_keys(stat)
    if len(set(keys).intersection(set(seen))) != 0:
        return True
    else:
        return False

def dedupe_stats(stats, seen):
    final = []
    for stat in stats:
        if not been_seen(stat, seen):
            seen += [build_key(stat)]
            final.append(stat)
    return final

def dedupe_and_add(stats, list):
    real_stats = dedupe_stats(stats, list)
    if real_stats:
        return reduce(lambda x,y: x+y, real_stats)
    else:
        return reporting_models.StatsModel() 

    



def chunks(list, chunk_size):
    '''Generator function that creates chunk_size lists from list
    '''
    for idx in xrange(0, len(list), chunk_size):
        yield list[idx:idx+chunk_size]

