# <<<<<<< HEAD
# import urllib
# import urllib2
# from hashlib import sha1
# from hmac import new as hmac
# 
# from datetime import datetime, date
# from scraper import Scraper, ScraperSite
# 
# class InMobiScraper(Scraper):
#     
#     NETWORK_NAME = 'inmobi'
#     API_URL = 'http://publisherapi.inmobi.com'
#     PLATFORM = 'all'
#     
#     def __init__(self, credentials):
#         if credentials['network'] != self.NETWORK_NAME:
#             raise "Invalid credentials.  Attempting to use %s credentials for an InMobi scraper" % credentials.network
#         super(InMobiScraper, self).__init__(credentials)
#         
#     def get_site_stats(self, start_date, end_date=None):
#         if end_date is None:
#             end_date = start_date
#         url = ("/pubData-1.0/extern/reports/" + self.username
#                + "/ad-view/all/"+ self.PLATFORM +"/publisher.xml?fromDate="
#                + start_date.strftime("%d%b%Y").lower() + "&toDate="
#                + end_date.strftime("%d%b%Y").lower() + "&filter=site")
#         full_url = self.API_URL + url
#         time = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
#         request_string = "GET\n" + time + "\n" + url
#         encoded_url = hmac(self.password, request_string, sha1).digest().encode('base64')[:-1]
#         req_dict = {'Authorization' : "Inmobi WS token :" + encoded_url,
#                     'Date' : time, 'x-data-user' : self.username}
#         # Might need to be a GET request instead of a POST request
#         req = urllib2.Request(full_url, urllib.urlencode(req_dict))
#         
#         return urllib2.urlopen(req)
#         
#         
# # for testing
# if __name__ == '__main__':
#     nc = {}
#     # access_id
#     nc['username'] = '4028cb8b2b617f70012b792fe65e00a2'
#     # secret_key
#     nc['password'] = '84585161'
#     nc['network'] = 'inmobi'
#     scraper = InMobiScraper(nc)
#     print scraper.get_site_stats(date.today())
# =======
import base64
import hashlib
import hmac
import time
import urllib2

from datetime import datetime
from datetime import date

from scraper import Scraper, ScraperSite

#TODO This needs a lot of work, I have no idea what it's doing
class NetworkCredentials:
    pass

class InMobiScraper(Scraper):

    NETWORK_NAME = 'inmobi'
    API_URL = 'http://publisherapi.inmobi.com'
    SITE_STAT_URL = '/pubData-1.0/extern/reports/%(username)s/ad-view/all/%(platform)s/publisher.xml?fromDate=%(start_date)s&toDate=%(end_date)s&filter=site'
    # TIMEZONE is included in DATE_FMT
    DATE_FMT = '%a, %d %b %Y %H:%M:%S PST'
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

            digest = hmac.new(self.password, url, hashlib.sha1).digest()

            self.token = base64.encodestring(digest)
            print self.token
            req = urllib2.Request(full_url)
            req.add_header('Authorization', 'Inmobi WS token :%s' % self.token)
            req.add_header('Date', now)
            req.add_header('x-data-user', self.username)
            return req
        self.get_stats_request = get_stats_request

    def get_site_stats(self, start_date, end_date=None):
        req = self.get_stats_request(start_date, end_date)
        resp = urllib2.urlopen(req)
        line = resp.read()
        print line


# for testing
if __name__ == '__main__':
    nc = NetworkCredentials()
    # access_id
    nc.username = '4028cb8b2b617f70012b792fe65e00a2'
    # secret_key
    nc.password = '84585161'
    nc.network = 'inmobi'
    scraper = InMobiScraper(nc)
    print scraper.get_site_stats(date.today())
