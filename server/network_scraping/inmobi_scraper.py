import base64
import hashlib
import hmac
import time
import urllib2

from datetime import datetime

from scraper import Scraper, ScraperSite

#TODO This needs a lot of work, I have no idea what it's doing


class InMobiScraper(Scraper):

    NETWORK_NAME = 'inmobi'
    API_URL = 'http://publisherapi.inmobi.com'
    SITE_STAT_URL = '/pubData-1.0/extern/reports/%(username)s/ad-view/all/%(platform)s/publisher.xml?fromDate=%(start_date)s&toDate=%(end_date)s&filter=site'
    DATE_FMT = '%a, %d %b %H:%M:%S %Z'

    def __init__(self, credentials, platform):
        self.platform = platform
        super(InMobiScraper, self).__init__(credentials)

    def authenticate(self):
        '''the inmobi token is generated each time, all authenticate can do is 
        prep everything so that the token generation is hella easy '''
        self.token = None
        def get_stats_request(start_date, end_date):
            ''' Each request needs an individual token and things
            so each time we want to make a request, call this function
            which builds it and does magic shit '''
            start_str = start_date.strftime('%d%b%Y').lower()
            end_str = end_date.strftime('%d%b%Y').lower()
            auth_dict = dict(username = self.username, platform = self.platform, start_date = start_str, end_date = end_str)
            url = self.SITE_STAT_URL % auth_dict
            now = datetime.now().strftime(self.DATE_FMT)
            full_url = self.API_URL + url

            # I'm not sure which is right, java uses the uncommented but
            # it just doesn't feel right.  Who knows - will test both
            final_str = 'GET\n' + now + '\n' + url
            #final_str = 'GET\n' + now + '\n' + full_url

            digest = hmac.new(self.password, url, hashlib.sha1)
            self.token = base64.encodestring(digest)
            req = urllib2.Request(full_url)
            req.add_header('Authorization', 'Inmobi WS token :%s' % self.token)
            req.add_header('Date', now)
            req.add_header('x-data-user', self.username)
            return req
        self.get_stats_request = get_stats_request

    def get_site_stats(self, start_date, end_date):
        req = self.get_stats_request(start_date, end_date)
        resp = urllib2.urlopen(req)
        line = resp.read()
        print line



        
