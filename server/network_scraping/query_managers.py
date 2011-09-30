import os, sys
sys.path.append(os.environ['PWD'])

from network_scraping.models import AdNetworkLoginInfo, AdNetworkAppMapper, AdNetworkScrapeStats

from publisher.models import App

# Query functions
''' Get the aggregate stats for the different apps given an account '''
def get_ad_network_totals(account):
    for l in AdNetworkLoginInfo.all().filter('account =', account):
        for n in AdNetworkAppMapper.all().filter('ad_network_login =', l):
            yield n

''' Get the AdNetworkStats for a given ad_network_app_mapper sorted chronologically by day, newest first (decending order) '''
def get_ad_network_app_stats(ad_network_app_mapper):
    q = AdNetworkScrapeStats.all()
    q.filter('ad_network_app_mapper =', ad_network_app_mapper)
    q.order('-date')
    return q
    
def get_jump_tap_pub_id(app_name, login_info):
    query = App.all()
    query.filter('name =', app_name)
    query.filter('account =', login_info.account)
    publisher_id = query.get()

    if publisher_id:
        return publisher_id.network_config.jumptap_pub_id
    else:
        return None
        
def get_ad_network_app_mapper(publisher_id, login_info):
    query = AdNetworkAppMapper.all()
    query.filter('ad_network_login =', login_info)
    query.filter('publisher_id =', publisher_id)
    return query.get()