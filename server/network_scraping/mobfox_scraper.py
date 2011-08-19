import urllib2
import urllib
import time
import datetime
from xml.dom import minidom

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass

def mobfox_scraper(network_credential, from_date, to_date):
    some_dict ={"api_key": network_credential.api_key, "publisher_id": network_credential.publisher_id, "start_date": from_date, "end_date": to_date}
    
    req = urllib2.Request('http://account.mobfox.com/reporting_api.php?'+urllib.urlencode(some_dict))
    response = urllib2.urlopen(req)
    dom = minidom.parseString(response.read())
        
    nsr = NetworkScrapeRecord()
    nsr.impressions = dom.getElementsByTagName("impressions")[0].childNodes[0].nodeValue
    nsr.clicks = dom.getElementsByTagName("clicks")[0].childNodes[0].nodeValue
    nsr.net_revenue = dom.getElementsByTagName("earnings")[0].childNodes[0].nodeValue
    nsr.ecpm = dom.getElementsByTagName("ecpm")[0].childNodes[0].nodeValue
    nsr.ctr = dom.getElementsByTagName("ctr")[0].childNodes[0].nodeValue
    nsr.app_name = dom.getElementsByTagName("type")[0].childNodes[0].nodeValue.split("Publisher Report: ")[1]
    
    return nsr
    
    #print nsr.impressions, ' ', nsr.clicks, ' ', nsr.net_revenue, ' ', nsr.ecpm, ' ', nsr.ctr, ' ', nsr.app_name
        
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.api_key='e64d04079c63c14644fc9690a925c8af'
    nc.publisher_id='fb8b314d6e62912617e81e0f7078b47e'
    mobfox_scraper(nc, time.mktime(datetime.date(2011,8,10).timetuple()),time.mktime(datetime.date(2011,8,11).timetuple()))