import urllib
import urllib2
from hashlib import sha1
from hmac import new as hmac

from datetime import datetime, date
from scraper import Scraper, ScraperSite

class InMobiScraper(Scraper):
    
    NETWORK_NAME = 'inmobi'
    API_URL = 'http://publisherapi.inmobi.com'
    PLATFORM = 'all'
    
    def __init__(self, credentials):
        if credentials['network'] != self.NETWORK_NAME:
            raise "Invalid credentials.  Attempting to use %s credentials for an InMobi scraper" % credentials.network
        super(InMobiScraper, self).__init__(credentials)
        
    def get_site_stats(self, start_date, end_date=None):
        if end_date is None:
            end_date = start_date
        url = ("/pubData-1.0/extern/reports/" + self.username
               + "/ad-view/all/"+ self.PLATFORM +"/publisher.xml?fromDate="
               + start_date.strftime("%d%b%Y").lower() + "&toDate="
               + end_date.strftime("%d%b%Y").lower() + "&filter=site")
        full_url = self.API_URL + url
        time = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        request_string = "GET\n" + time + "\n" + url
        encoded_url = hmac(self.password, request_string, sha1).digest().encode('base64')[:-1]
        req_dict = {'Authorization' : "Inmobi WS token :" + encoded_url,
                    'Date' : time, 'x-data-user' : self.username}
        # Might need to be a GET request instead of a POST request
        req = urllib2.Request(full_url, urllib.urlencode(req_dict))
        
        return urllib2.urlopen(req)
        
        
# for testing
if __name__ == '__main__':
    nc = {}
    # access_id
    nc['username'] = '4028cb8b2b617f70012b792fe65e00a2'
    # secret_key
    nc['password'] = '84585161'
    nc['network'] = 'inmobi'
    scraper = InMobiScraper(nc)
    print scraper.get_site_stats(date.today())
