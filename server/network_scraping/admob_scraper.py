import urllib
import urllib2
import json
import time

from scraper import Scraper, ScraperSite

#gets all sites, but would be possible to specify, not broken down by adunit.
class NetworkConfidential():
    pass


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
        if credentials.network != self.NETWORK_NAME:
            raise "Invalid credentials.  Attempting to use %s credentials for an AdMob scraper" % credentials.network
        self.client_key = credentials.api_key
        super(AdMobScraper, self).__init__(credentials)
        # authenticate on creation
        self.authenticate()

    def authenticate(self):
        auth_dict = dict(client_key=self.client_key,
                         email = self.username,
                         password = self.password,
                         )
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

    def get_site_stats(self, start_date, end_date, ids=None, obj_dim=None, time_dim=None, order_by=None):
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

        query_dict = dict(start_date = start_date, end_date = end_date)
        query_dict.update(self.auth_dict)
        req = urllib2.Request(str(self.SITE_STAT_URL + '?' + query_string + '&' + urllib.urlencode(query_dict)))
        resp = urllib2.urlopen(req)
        stats = json.load(urllib2.urlopen(req))
        #TODO make stats not a json dict lol
        return stats




def admob_scraper(nc, from_date, to_date):
    req = urllib2.Request('https://api.admob.com/v2/auth/login', urllib.urlencode({'client_key': nc.client_key, 'email': nc.email, 'password': nc.password}))
    token = json.load(urllib2.urlopen(req))['data']['token']
    
    req = urllib2.Request('http://api.admob.com/v2/site/search?' + urllib.urlencode({'client_key': nc.client_key, 'token': token}))
    response = urllib2.urlopen(req)
        
    site_ids = []
    for site in json.loads(response.readline())['data']:
        site_ids.append(site['id'])

    scrape_records = {}
    for site_id in site_ids:
        req = urllib2.Request('http://api.admob.com/v2/site/stats?' + urllib.urlencode({'client_key': nc.client_key, 'token': token, 'site_id': site_id,
        'start_date': from_date, 'end_date': to_date}))
        response = urllib2.urlopen(req)

        stats = json.loads(response.readline())['data']
        print stats
                
        #nsr = NetworkScrapeRecord()
        #nsr.impressions = stats['impressions']
        #nsr.clicks = stats['clicks']
        #nsr.net_revenue = stats['revenue']
        #nsr.requests = stats['requests']
        #nsr.ecpm = stats['ecpm']
        #nsr.fill_rate = stats['fill_rate']
        #nsr.ctr = stats['ctr']
                
        #scrape_records[site_id] = nsr
        
    return scrape_records
    
    # for key in scrape_records.keys():
    #     print key
    #     print scrape_records[key].impressions, ' ', scrape_records[key].clicks, ' ', scrape_records[key].net_revenue, ' ', scrape_records[key].requests, ' ', scrape_records[key].ecpm, ' ', scrape_records[key].fill_rate, ' ', scrape_records[key].ctr

if __name__ == '__main__':
    nc = NetworkConfidential()
    nc2 = NetworkConfidential
    nc2.account = 3
    nc2.username = nc.email ='njamal@stanford.edu'
    nc2.password = nc.password ='xckjhfn3xprkxksm'
    nc2.api_key = nc.client_key = 'k907a03ee39cecb699b5ad45c5eded01'
    nc2.network = 'admob'
    scraper = AdMobScraper(nc2)
    print scraper.get_site_stats('2011-07-24','2011-07-25')
    time.sleep(1)
    admob_scraper(nc, '2011-07-24','2011-07-25')
