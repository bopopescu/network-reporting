import urllib
import urllib2
import json
import logging
import sys
import time

from datetime import date, timedelta
sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
from ad_network_reports.scrapers.scraper import Scraper, ScraperSite, \
        NetworkConfidential
from ad_network_reports.scrapers.network_scrape_record import \
        NetworkScrapeRecord

def admob_list_encode(sequence, var_name):
    list_var_name = var_name + '[]'
    ret_str = ''
    for index, elt in enumerate(sequence):
        ret_str += list_var_name + '=' + elt
        if index + 1 != len(sequence):
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

        response = json.load(urllib2.urlopen(req))
        if response['errors'] == []:
            self.token = response['data']['token']
            self.auth_dict = dict(client_key = self.client_key,
                    token=self.token)
        else:
            logging.error(response['errors'])
            raise Exception("\n".join([r['msg'] for r in response['errors']]))

    def test_login_info(self):
        """Login info has already been tested in the constructor (via the
        authenticate method) so we pass.

        Return None.
        """
        pass

    def get_sites(self):
        req = urllib2.Request(self.SITE_SEARCH_URL + '?' +
                urllib.urlencode(self.auth_dict))
        sites = []
        site_data = json.load(urllib2.urlopen(req))
        #TODO pagination stuff with the 'page' part
        for site in site_data['data']:
            new_dict = {}
            for key, value in site.iteritems():
                new_dict[str(key)] = value
            sites.append(ScraperSite(**new_dict))
        return sites

    def get_site_stats(self, start_date):
        end_date = start_date

        ids = [str(site.identifier) for site in self.get_sites()]
        # Admob API has a rate limit, don't piss them off
        time.sleep(1)

        if len(ids) > 1:
            query_string = admob_list_encode(ids, 'site_id')
        else:
            query_string = 'site_id=%s' % ids[0]

        query_dict = dict(start_date = start_date.strftime("%Y-%m-%d"),
                          end_date = end_date.strftime("%Y-%m-%d"),
                          object_dimension = 'site')
        query_dict.update(self.auth_dict)
        req = urllib2.Request(str(self.SITE_STAT_URL + '?' + query_string + '&'
            + urllib.urlencode(query_dict)))

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

if __name__ == '__main__':
    NC = NetworkConfidential()
    NC.username = 'adnetwork@com2usamerica.com'
    NC.password = '4w47m82l5jfdqw1x'
    NC.client_key = 'ka820827f7daaf94826ce4cee343837a'
    NC.ad_network_name = 'admob'
    SCRAPER = AdMobScraper(NC)
    print SCRAPER.get_site_stats(date.today()) #- timedelta(days=2))
