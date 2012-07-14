import os
import urllib
import urllib2
try:
    import json
except ImportError:
    import simplejson as json
import logging
import sys
import time

# Paths only needed for testing
if os.path.exists('/home/ubuntu/'):
    sys.path.append('/home/ubuntu/mopub/server')
else:
    # Assumes it is being called from the server dir
    sys.path.append(os.environ['PWD'])
from ad_network_reports.scrapers.scraper import Scraper, ScraperSite, \
        NetworkConfidential
from ad_network_reports.scrapers.network_scrape_record import \
        NetworkScrapeRecord
from ad_network_reports.scrapers.unauthorized_login_exception import \
        UnauthorizedLogin
from datetime import date, timedelta

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
            raise UnauthorizedLogin("\n".join([r['msg'] for r in response[
                'errors']]))

    def test_login_info(self):
        """Login info has already been tested in the constructor (via the
        authenticate method) so we pass.

        Return None.
        """
        pass

    def get_sites(self):
        page = 1
        page_total = 999
        sites = []
        while page <= page_total:
            self.auth_dict['page'] = page
            req = urllib2.Request(self.SITE_SEARCH_URL + '?' +
                    urllib.urlencode(self.auth_dict))
            site_data = json.load(urllib2.urlopen(req))
            page_total = site_data['page']['total']
            print '%s / %s' % (page, page_total)
            for site in site_data['data']:
                new_dict = {}
                for key, value in site.iteritems():
                    new_dict[str(key)] = value
                sites.append(ScraperSite(**new_dict))
            page += 1
        return sites

    def get_site_stats(self, start_date):
        end_date = start_date

        ids = [str(site.identifier) for site in self.get_sites()]
        # Admob API has a rate limit, don't piss them off
        time.sleep(1)

        if len(ids) > 1:
            query_string = admob_list_encode(ids, 'site_id')
        elif len(ids) == 1:
            query_string = 'site_id=%s' % ids[0]
        else:
            return []

        query_dict = dict(start_date = start_date.strftime("%Y-%m-%d"),
                          end_date = end_date.strftime("%Y-%m-%d"),
                          object_dimension = 'site')
        query_dict.update(self.auth_dict)

        records = []
        page = 1
        page_total = 999
        while page <= page_total:
            query_dict['page'] = page
            req = urllib2.Request(str(self.SITE_STAT_URL + '?' + query_string +
                '&' + urllib.urlencode(query_dict)))

            site_stats = json.load(urllib2.urlopen(req))
            page_total = site_stats['page']['total']
            print '%s / %s' % (page, page_total)

            if site_stats['data']:
                for stats in site_stats['data']:
                    nsr = NetworkScrapeRecord(revenue = stats['revenue'],
                                              attempts = stats['requests'],
                                              impressions = stats['impressions'],
                                              clicks = stats['clicks'])

                    if 'site_id' in stats:
                        nsr.app_tag = stats['site_id']
                    else:
                        nsr.app_tag = ids[0]
                    records.append(nsr)
            page += 1

        return records

if __name__ == '__main__':
    NC = NetworkConfidential()
    NC.username = 'developers@animoca.com'
    NC.password = '5zfy6wmbx4kcgflq'
    NC.client_key = 'k0df241c82bfe3c34d8fe7750c1705e6'
    NC.ad_network_name = 'admob'
    SCRAPER = AdMobScraper(NC)
    all_stats = SCRAPER.get_site_stats(date.today() - timedelta(days=2))
    print len(all_stats)
    for stats in all_stats:
        print stats

