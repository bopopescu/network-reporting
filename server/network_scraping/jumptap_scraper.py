import urllib2
import urllib

from datetime import date
from scraper import Scraper, ScraperSite

class NetworkScrapeRecord(object):
    pass

class JumpTapScraper(Scraper):
    
    NETWORK_NAME = 'jumptap'
    SITE_STAT_URL = 'https://pa.jumptap.com/pa-2.0/pub-services/v10/report.html'

    def __init__(self, credentials):
        if credentials['network'] != self.NETWORK_NAME:
            raise "Invalid credentials.  Attempting to use %s credentials for an JumpTap scraper" % credentials['network']
        super(JumpTapScraper, self).__init__(credentials)

    # Note: a date range is not supported
    def get_site_stats(self, from_date, to_date=None):
        if to_date is None:
            to_date = from_date
           
        query_dict = {"user": self.username,
                          "pass": self.password,
                          "fromDate": from_date.strftime("%m/%d/%Y"),
                          "toDate": to_date.strftime("%m/%d/%Y"),
                          "groupBy": "spot"}

        req = urllib2.Request(self.SITE_STAT_URL,
                              urllib.urlencode(query_dict))
        response = urllib2.urlopen(req)

        headers = response.readline().split(',')

        request_index = headers.index('Requests')
        imp_index = headers.index('Paid Impressions')
        click_index = headers.index('Clicks')
        cpm_index = headers.index('Net eCPM')
        app_index = headers.index('Site')
        adunit_index = headers.index('Spot')

        # dict stores list of nsrs for each 'spot' or ad unit where the key in the dict is the app
        scrape_records = {}
        for line in response:
            vals = line.split(',')
            if vals[0] != 'Totals':
                nsr = NetworkScrapeRecord()
                nsr.requests = int(vals[request_index])
                nsr.impressions = int(vals[imp_index])
                nsr.clicks = int(vals[click_index])
                nsr.cpm = float(vals[cpm_index])
                nsr.app_name = vals[app_index]
                nsr.adunit_name = vals[adunit_index]
                # doesn't work for a date range
                if nsr.app_name not in scrape_records:
                    scrape_records[nsr.app_name] = [nsr]
                else:
                    scrape_records[nsr.app_name] += [nsr]
        
        records = []
        for k, v in scrape_records.iteritems():
            nsr = NetworkScrapeRecord()
            nsr.attempts = 0
            nsr.impressions = 0
            nsr.clicks = 0
            cost = 0
            
            for n in v:
                nsr.attempts += n.requests
                nsr.impressions += n.impressions
                nsr.clicks += n.clicks
                cost += n.cpm * n.impressions
               
            nsr.fill_rate = nsr.impressions / float(nsr.attempts)
            nsr.ctr = nsr.clicks / float(nsr.impressions)
            nsr.cpm = cost / float(nsr.impressions)
            
            nsr.app_tag = v[0].app_name
            records.append(nsr)

        return records

# for testing   
if __name__ == '__main__':
    nc = {}
    nc['username'] = 'vrubba'
    nc['password'] = 'fluik123!'
    nc['network'] = 'jumptap'
    scraper = JumpTapScraper(nc)
    print scraper.get_site_stats(date.today())
    
    
