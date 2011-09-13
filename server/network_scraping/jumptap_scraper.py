import urllib2
import urllib
import json

from scraper import Scraper, ScraperSite

#can specify app or not specify app, breaks down by adunit.

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass

class JumpTapScraper(Scraper): 
    NETWORK_NAME = 'jumptap'
    SITE_STAT_URL = 'https://pa.jumptap.com/pa-2.0/pub-services/v10/report.html'

    def __init__(self, credentials):
        if credentials.network != self.NETWORK_NAME:
            raise "Invalid credentials.  Attempting to use %s credentials for an AdMob scraper" % credentials.network
        super(JumpTapScraper, self).__init__(credentials)

    def get_site_stats(self, from_date, to_date):
        query_dict = {"user": self.username,
                          "pass": self.password,
                          "fromDate": from_date,
                          "toDate": to_date,
                          "groupBy": "spot"}

        req = urllib2.Request(self.SITE_STAT_URL,
                              urllib.urlencode(query_dict))
        response = urllib2.urlopen(req)

        headers = response.readline().split(',')

        imp_index = headers.index('Paid Impressions')
        click_index = headers.index('Clicks')
        net_rev_index = headers.index('Net Revenue$')
        requests_index = headers.index('Requests')
        cpc_index = headers.index('Net Cost Per Click')
        app_index = headers.index('Site')
        adunit_index = headers.index('Spot')

        scrape_records = {}
        for line in response:
            vals = line.split(',')
            if vals[0] != 'Totals':
                nsr = NetworkScrapeRecord()
                nsr.impressions = vals[imp_index]
                nsr.clicks = vals[click_index]
                nsr.net_revenue = vals[net_rev_index]
                nsr.requests = vals[requests_index]
                nsr.cpc = vals[cpc_index]
                nsr.app_name = vals[app_index]
                nsr.adunit_name = vals[adunit_index]
                # key doesn't include the date so we can't include more than one day
                # in the time span otherwise it will only grab the last one
                scrape_records['%s||%s' % (vals[app_index], vals[adunit_index])] = nsr

        return scrape_records
   
def jumptap_scraper(network_credential, from_date, to_date):  
    some_dict ={"user": network_credential.username, "pass": network_credential.password, "fromDate": from_date, "toDate": to_date, "groupBy": "spot"}
 
    if network_credential.app_name:
        some_dict['sites'] = network_credential.app_name
    
    req = urllib2.Request('https://pa.jumptap.com/pa-2.0/pub-services/v10/report.html?'+urllib.urlencode(some_dict))
    response = urllib2.urlopen(req)
    
    headers = response.readline().split(',')
    
    imp_index = headers.index('Paid Impressions')
    click_index = headers.index('Clicks')
    net_rev_index = headers.index('Net Revenue$')
    requests_index = headers.index('Requests')
    cpc_index = headers.index('Net Cost Per Click')
    app_index = headers.index('Site')
    adunit_index = headers.index('Spot')
    
    scrape_records = {}
    for line in response:
        vals = line.split(',')
        if vals[0] != 'Totals':
            nsr = NetworkScrapeRecord()
            nsr.impressions = vals[imp_index]
            nsr.clicks = vals[click_index]
            nsr.net_revenue = vals[net_rev_index]
            nsr.requests = vals[requests_index]
            nsr.cpc = vals[cpc_index]
            nsr.app_name = vals[app_index]
            nsr.adunit_name = vals[adunit_index]
            scrape_records['%s||%s'%(vals[app_index], vals[adunit_index])] = nsr
            
    # return scrape_records
    for key in scrape_records.keys():
        print key
        print scrape_records[key].impressions, ' ', scrape_records[key].clicks, ' ', scrape_records[key].net_revenue, ' ', scrape_records[key].requests, ' ', scrape_records[key].cpc, ' ', scrape_records[key].app_name, ' ', scrape_records[key].adunit_name
    
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.account = 3
    nc.username = 'vrubba'
    nc.password = 'fluik123!'
    nc.app_name = None
    #nc.app_name = 'pa_fluik_entertain_office_jerk_fre_drd_app'
    nc.network = 'jumptap'
    scraper = JumpTapScraper(nc)
    print scraper.get_site_stats('7/1/2011','7/1/2011')
    jumptap_scraper(nc, '7/1/2011','7/1/2011')
    
    
