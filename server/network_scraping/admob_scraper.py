import urllib
import urllib2
import json
import time

from datetime import date
from scraper import Scraper, ScraperSite
from network_scrape_record import NetworkScrapeRecord

def admob_list_encode(list, var_name):
    list_var_name = var_name + '[]'
    ret_str = ''
    for i,elt in enumerate(list):
        ret_str += list_var_name + '=' + elt
        if i+1 != len(list):
            ret_str += '&'
    return ret_str

class AdMobScraper(Scraper):

    NETWORK_NAME = 'admob'
    API_URL = 'http://api.admob.com'
    AUTH_URL = 'https://api.admob.com/v2/auth/login'
    SITE_SEARCH_URL = API_URL + '/v2/site/search'
    SITE_STAT_URL = API_URL + '/v2/site/stats'

    def __init__(self, credentials):
        self.client_key = credentials.client_key
        super(AdMobScraper, self).__init__(credentials)
        
        self.authenticate()

    def authenticate(self):
        auth_dict = dict(client_key = self.client_key,
                         email = self.username,
                         password = self.password)
        req = urllib2.Request(self.AUTH_URL, urllib.urlencode(auth_dict))
        self.token = json.load(urllib2.urlopen(req))['data']['token']
        self.auth_dict = dict(client_key = self.client_key, token=self.token)
        #TODO mechanize stuff here

    def get_sites(self):
        req = urllib2.Request(self.SITE_SEARCH_URL + '?' + urllib.urlencode(self.auth_dict))
        sites = []
        site_data = json.load(urllib2.urlopen(req))
        #TODO pagination stuff with the 'page' part
        for site in site_data['data']:
            new_dict = {}
            for k,v in site.iteritems():
                new_dict[str(k)] = v
            sites.append(ScraperSite(**new_dict))
        return sites

    def get_site_stats(self, start_date, end_date=None, ids=None, obj_dim=None, time_dim=None, order_by=None):
        if end_date is None:
            end_date = start_date
        
        if ids is None:
            ids = [str(site.id) for site in self.get_sites()]
            # Admob API has a rate limit, don't piss them off
            time.sleep(1)
        elif not isinstance(ids, list):
            ids = [ids]

        if len(ids) > 1:
            query_string = admob_list_encode(ids, 'site_id')
        else:
            query_string = 'site_id=%s' % ids[0]

        query_dict = dict(start_date = start_date.strftime("%Y-%m-%d"),
                          end_date = end_date.strftime("%Y-%m-%d"),
                          object_dimension = 'site')
        query_dict.update(self.auth_dict)
        req = urllib2.Request(str(self.SITE_STAT_URL + '?' + query_string + '&' + urllib.urlencode(query_dict)))

        #TODO pagination stuff with the 'page' part
        site_stats = json.load(urllib2.urlopen(req))
        
        records = []
        for stats in site_stats['data']:
            nsr = NetworkScrapeRecord(revenue = stats['revenue'],
                                      attempts = stats['requests'],
                                      impressions = stats['impressions'],
                                      fill_rate = stats['fill_rate'],
                                      clicks = stats['clicks'],
                                      ctr = stats['ctr'],
                                      ecpm = stats['ecpm'])
            
            if 'site_id' in stats:
                nsr.app_tag = stats['site_id']
            else:
                nsr.app_tag = ids[0]
            records.append(nsr)
            
        return records
        
class NetworkConfidential:
    pass

# for testing
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.username = 'njamal@stanford.edu'
    nc.password = 'xckjhfn3xprkxksm'
    nc.client_key = 'k907a03ee39cecb699b5ad45c5eded01'
    nc.ad_network_name = 'admob'
    scraper = AdMobScraper(nc)
    print scraper.get_site_stats(date.today())
