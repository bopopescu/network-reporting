import base64
import hashlib
import hmac
import time
import urllib2

from datetime import datetime
from datetime import date
from xml.dom.minidom import parseString

from scraper import Scraper, ScraperSite

#TODO This needs a lot of work, I have no idea what it's doing
class NetworkCredentials:
    pass

class InMobiScraper(Scraper):

    NETWORK_NAME = 'inmobi'
    API_URL = 'http://publisherapi.inmobi.com'
    SITE_STAT_URL = '/pubData-1.0/extern/reports/%(username)s/ad-view/all/%(platform)s/publisher.xml?fromDate=%(start_date)s&toDate=%(end_date)s&filter=site'
    # TIMEZONE is included in DATE_FMT
    DATE_FMT = '%a, %d %b %Y %H:%M:%S PDT'
    PLATFORM = 'all'

    def __init__(self, credentials):
        super(InMobiScraper, self).__init__(credentials)
	self.authenticate()

    def authenticate(self):
        '''the inmobi token is generated each time, all authenticate can do is 
        prep everything so that the token generation is hella easy '''
        self.token = None
        def get_stats_request(start_date, end_date=None):
            ''' Each request needs an individual token and things
            so each time we want to make a request, call this function
            which builds it and does magic shit '''
            if end_date is None:
                end_date = start_date

            start_str = start_date.strftime('%d%b%Y').lower()
            end_str = end_date.strftime('%d%b%Y').lower()
            auth_dict = dict(username = self.username, platform = self.PLATFORM, start_date = start_str, end_date = end_str)
            url = self.SITE_STAT_URL % auth_dict
            now = datetime.now().strftime(self.DATE_FMT)
            full_url = self.API_URL + url

            # I'm not sure which is right, java uses the uncommented but
            # it just doesn't feel right.  Who knows - will test both
            final_str = 'GET\n' + now + '\n' + url
            #final_str = 'GET\n' + now + '\n' + full_url

            encoded_url = hmac.new(self.password, final_str, hashlib.sha1).digest().encode('base64')[:-1]

            req = urllib2.Request(full_url)
            req.add_header('Authorization', 'Inmobi WS token :%s' % encoded_url)
            req.add_header('Date', now)
            req.add_header('x-data-user', self.username)
            return req
        self.get_stats_request = get_stats_request

    def get_site_stats(self, start_date, end_date=None):
        req = self.get_stats_request(start_date, end_date)
        resp = urllib2.urlopen(req)
        line = resp.read()
        dom = parseString(line)
        
        reports = dom.getElementsByTagName("reports")[0]
        for node in reports.childNodes:
            

# for testing
if __name__ == '__main__':
    nc = NetworkCredentials()
    # access_id
    nc.username = '4028cb8b2b617f70012b792fe65e00a2'
    # secret_key
    nc.password = '84585161'
    nc.ad_network_name = 'inmobi'
    scraper = InMobiScraper(nc)
    print scraper.get_site_stats(date(2010, 10, 20), date(2010, 11, 15))
