import os, sys
sys.path.append(os.environ['PWD'])

from network_scraping.models import AdNetworkLoginInfo, AdNetworkAppMapper, AdNetworkScrapeStats

from publisher.models import App

class AdNetworkReportQueryManager(CachedQueryManager):

    def __init__(self, account=None, offline=True):
        if isinstance(account, db.Key):
            self.account = account
        elif isinstance(account, db.Model):
            self.account = account.key()
        elif account is None:
            self.account = None
        else:
            self.account = db.Key(account)
        
    def get_ad_network_totals():
        """ Get the aggregate stats for the different apps given an account """
        for l in AdNetworkLoginInfo.all().filter('account =', self.account):
            for n in AdNetworkAppMapper.all().filter('ad_network_login =', l):
                yield n

    def get_ad_network_app_stats(ad_network_app_mapper):
        """ Get the AdNetworkStats for a given ad_network_app_mapper sorted
        chronologically by day, newest first (decending order) """
        q = AdNetworkScrapeStats.all()
        q.filter('ad_network_app_mapper =', ad_network_app_mapper)
        q.order('-date')
        return q
        
    def get_ad_network_app_mapper(publisher_id, login_info):
        """ Get the AdNetworkAppMapper for a given publisher id and 
        login info """
        query = AdNetworkAppMapper.all()
        query.filter('ad_network_login =', login_info)
        query.filter('publisher_id =', publisher_id)
        return query.get()
        
def get_pub_id(pub_id, login_info):
    return pub_id

def get_jump_tap_pub_id(app_name, login_info):
    query = App.all()
    query.filter('name =', app_name)
    query.filter('account =', self.account)
    publisher_id = query.get()

    if publisher_id:
        return publisher_id.network_config.jumptap_pub_id
    else:
        return None