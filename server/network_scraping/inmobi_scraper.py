import base64
from hashlib import sha1
from hmac import new as hmac
import json
import logging
import time
import urllib2

from datetime import datetime, date, timedelta
from xml.dom.minidom import parseString

from network_scrape_record import NetworkScrapeRecord
from scraper import Scraper, ScraperSite

class InMobiScraper(Scraper):

    NETWORK_NAME = 'inmobi'
    API_URL = 'http://publisherapi.inmobi.com'
    SITE_STAT_URL = '/pubData-1.0/extern/reports/%(username)s/ad-view/all/%(platform)s/publisher.json?fromDate=%(start_date)s&toDate=%(end_date)s&filter=site'
    # TIMEZONE is included in DATE_FMT
    DATE_FMT = '%a, %d %b %Y %H:%M:%S PDT'
    PLATFORM = 'all'
    
    def test_login_info(self):
        """Test the Access ID and Secret Key.
        
        Raise a 403 error if Access ID or Secret Key are incorrect otherwise return None.
        """
        self.get_site_stats(date.today() - timedelta(days = 1))

    def get_site_stats(self, start_date):
        # Date can't be today
        end_date = start_date
        # range can't start and end on the same date for InMobi
        start_date -= timedelta(days = 1)

        start_str = start_date.strftime('%d%b%Y').lower()
        end_str = end_date.strftime('%d%b%Y').lower()
        auth_dict = dict(username = self.username, platform = self.PLATFORM, start_date = start_str, end_date = end_str)
        url = self.SITE_STAT_URL % auth_dict
        now = datetime.now().strftime(self.DATE_FMT)
        full_url = self.API_URL + url

        final_str = 'GET\n%s\n%s' % (now, url)

        # Strings are stored as unicode in appengine
        self.password = str(self.password)
        encoded_url = hmac(self.password, final_str, sha1).digest().encode('base64')[:-1]

        req = urllib2.Request(full_url)
        req.add_header('Authorization', 'Inmobi WS token :%s' % encoded_url)
        req.add_header('Date', now)
        req.add_header('x-data-user', self.username)
            
        resp = urllib2.urlopen(req)
        line = resp.read()
        print line
        if line.find('error') != -1:
            logging.error("Day range (%s to %s) selected for InMobi doesn\'t have any data. %s" % 
                    (start_date.strftime("%Y %m %d"), end_date.strftime("%Y %m %d"), dictionary['errors']))
            
        dictionary = json.loads(line)
                    
        reports_dicts = dictionary['data']['reports']
        reports = []
        for report_dict in reports_dicts:
            nsr = NetworkScrapeRecord(revenue = float(report_dict['earn']), attempts = int(report_dict['req']),
                                      impressions = int(report_dict['imp']), fill_rate = float(report_dict['fr']),
                                      clicks = int(report_dict['clk']), ctr = float(report_dict['ctr']),
                                      ecpm = float(report_dict['ecpm']), app_tag = str(report_dict['excol']))
            reports.append(nsr)
            
        return reports
        
# for testing
class NetworkCredentials:
    pass

if __name__ == '__main__':
    nc = NetworkCredentials()
    # access_id
    nc.username = '4028cb973099fe040130c2aa2a0904b5'
    # secret_key
    nc.password = '098233019949'
    nc.ad_network_name = 'inmobi'
    scraper = InMobiScraper(nc)
    print scraper.get_site_stats(date.today() - timedelta(days = 1))
