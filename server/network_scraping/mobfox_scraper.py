import urllib2
import urllib
import time
import datetime
from xml.dom import minidom

from network_scrape_record import NetworkScrapeRecord

''' One app stats returned per request sent. Can't break down by ad unit. '''
class MobFoxScraper(object):
    # API_KEY is MoPub specific
    API_KEY = 'e64d04079c63c14644fc9690a925c8af'
    
    def __init__(self, credentials):
        self.publisher_ids = credentials.publisher_ids
    
    def get_site_stats(self, from_date, to_date=None):
        if  to_date is None:
            to_date = from_date
        
        req_dict ={"api_key": self.API_KEY, "start_date": time.mktime(from_date.timetuple()), "end_date": time.mktime(to_date.timetuple())}
        
        reports = []
        for pub_id in self.publisher_ids:
            req_dict['publisher_id'] = pub_id
            req = urllib2.Request('http://account.mobfox.com/reporting_api.php?'+urllib.urlencode(req_dict))
            
            response = urllib2.urlopen(req)
            self.dom = minidom.parseString(response.read())
        
            nsr = NetworkScrapeRecord(impressions = self.get_value("impressions"),
                                      clicks = self.get_value("clicks"),
                                      net_revenue = self.get_value("earnings"),
                                      ecpm = self.get_value("ecpm"),
                                      ctr = self.get_value("ctr"),
                                      app_tag = pub_id)
    
            reports.append(nsr)
        
        return reports
    
    def get_value(self, name):
        self.dom.getElementsByTagName(name)[0].childNodes[0].nodeValue
    
class NetworkConfidential(object):
    pass
        
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.publisher_ids = ['fb8b314d6e62912617e81e0f7078b47e']
    scraper = MobFoxScraper(nc)
    print scraper.get_site_stats(datetime.date(2011,8,10))