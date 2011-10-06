import urllib2
import urllib
import time
from datetime import date, timedelta
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
            # range can't start and end on the same date for MobFox
            from_date -= timedelta(days = 1)
        
        req_dict ={"api_key" : self.API_KEY, "start_date" : time.mktime(from_date.timetuple()), "end_date" : time.mktime(to_date.timetuple()), "report_type" : 2}
        
        reports = []
        for pub_id in self.publisher_ids:
            req_dict['publisher_id'] = pub_id
            req = urllib2.Request('http://account.mobfox.com/reporting_api.php?'+urllib.urlencode(req_dict))
            
            response = urllib2.urlopen(req)
            self.dom = minidom.parseString(response.read())
        
            try:
                nsr = NetworkScrapeRecord(revenue = float(self.get_value("earnings")),
                                          attempts = 0, # We can't get the number of attempts / requests
                                          impressions = int(self.get_value("impressions")),
                                          fill_rate = 0.0, # We can't get this and we don't have # attempts so we can't calculate it
                                          clicks = int(self.get_value("clicks")),
                                          ecpm = float(self.get_value("ecpm")),
                                          ctr = float(self.get_value("ctr")),
                                          app_tag = pub_id)
                reports.append(nsr)
            except Exception as e:
                print ('Day range (%s to %s) selected for mobfox doesn\'t have any data' % 
                        (from_date.strftime("%Y %m %d"), to_date.strftime("%Y %m %d")))
                # logging.error()
        
        return reports
    
    def get_value(self, name):
        return self.dom.getElementsByTagName(name)[0].childNodes[0].nodeValue
    
class NetworkConfidential(object):
    pass
        
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.publisher_ids = ['fb8b314d6e62912617e81e0f7078b47e']
    scraper = MobFoxScraper(nc)
    print scraper.get_site_stats(date.today())