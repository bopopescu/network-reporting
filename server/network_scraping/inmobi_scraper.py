import base64
from hashlib import sha1
from hmac import new as hmac
import logging
import time
import urllib2

from datetime import datetime
from datetime import date, timedelta
from xml.dom.minidom import parseString

from network_scrape_record import NetworkScrapeRecord
from scraper import Scraper, ScraperSite

class InMobiScraper(Scraper):

    NETWORK_NAME = 'inmobi'
    API_URL = 'http://publisherapi.inmobi.com'
    SITE_STAT_URL = '/pubData-1.0/extern/reports/%(username)s/ad-view/all/%(platform)s/publisher.xml?fromDate=%(start_date)s&toDate=%(end_date)s&filter=site'
    # TIMEZONE is included in DATE_FMT
    DATE_FMT = '%a, %d %b %Y %H:%M:%S PDT'
    PLATFORM = 'all'

    def get_site_stats(self, start_date, end_date=None):
        # Date can't be today
        if end_date is None:
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
    
        # Unfortunately we can't get it back as a json dict since we're using python and
        # not PHP or Java which support the API so we must parse the xml
        self.dom = parseString(line)
    
        reports = []
        errors = self.dom.getElementsByTagName('error')
        if len(errors) == 0:   
            for app_stats in zip(self.get_data_list('req'), self.get_data_list('imp'), self.get_data_list('fr'),
                                 self.get_data_list('clk'), self.get_data_list('ctr'), self.get_data_list('ecpm'),
                                 self.get_data_list('excol')):
                nsr = NetworkScrapeRecord(attempts = int(app_stats[0]), impressions = int(app_stats[1]),
                                          fill_rate = float(app_stats[2]), clicks = int(app_stats[3]),
                                          ctr = float(app_stats[4]), ecpm = float(app_stats[5]),
                                          app_tag = str(app_stats[6]))
                reports.append(nsr)
        else:
            print ('Day range (%s to %s) selected for InMobi doesn\'t have any data' % 
                    (start_date.strftime("%Y %m %d"), end_date.strftime("%Y %m %d")))
            # logging.error()
            
        return reports
        
        
    def get_data_list(self, name):
        return [e.childNodes[0].data for e in self.dom.getElementsByTagName(name)]
        
# for testing
class NetworkCredentials:
    pass

if __name__ == '__main__':
    nc = NetworkCredentials()
    # access_id
    nc.username = '4028cb8b2b617f70012b792fe65e00a2'
    # secret_key
    nc.password = '84585161'
    nc.ad_network_name = 'inmobi'
    scraper = InMobiScraper(nc)
    print scraper.get_site_stats(date.today() - timedelta(days = 1))
