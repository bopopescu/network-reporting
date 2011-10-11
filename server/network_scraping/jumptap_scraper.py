import urllib2
import urllib

from datetime import date, timedelta
from scraper import Scraper, ScraperSite
from network_scrape_record import NetworkScrapeRecord

class JumpTapScraper(Scraper):
    
    NETWORK_NAME = 'jumptap'
    SITE_STAT_URL = 'https://pa.jumptap.com/pa-2.0/pub-services/v10/report.html'

    def test_login_info(self):
        """Test the username and password.
        
        Raise a 401 error if username or password are incorrect otherwise return None.
        """
        self.get_site_stats(date.today() - timedelta(days = 1))

    def get_site_stats(self, from_date):
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

        revenue_index = headers.index('Net Revenue$')
        request_index = headers.index('Requests')
        imp_index = headers.index('Paid Impressions')
        click_index = headers.index('Clicks')
        cpm_index = headers.index('Net eCPM')
        app_index = headers.index('Site')
        # adunit_index = headers.index('Spot')

        # dict stores list of nsrs for each 'spot' or ad unit where the key in the dict is the app
        scrape_records = {}
        for line in response:
            vals = line.split(',')
            if vals[0] != 'Totals':
                nsr = NetworkScrapeRecord(revenue = float(vals[revenue_index]),
                                          attempts = int(vals[request_index]),
                                          impressions = int(vals[request_index]),
                                          clicks = int(vals[click_index]),
                                          ecpm = float(vals[cpm_index]),
                                          app_tag = vals[app_index])
                # doesn't work for a date range
                if nsr.app_tag not in scrape_records:
                    scrape_records[nsr.app_tag] = [nsr]
                else:
                    scrape_records[nsr.app_tag] += [nsr]
        
        records = []
        for v in scrape_records.values():
            revenue = 0
            attempts = 0
            impressions = 0
            clicks = 0
            cost = 0
            
            for n in v:
                revenue += n.revenue
                attempts += n.attempts
                impressions += n.impressions
                clicks += n.clicks
                cost += n.ecpm * n.impressions
            
            nsr = NetworkScrapeRecord(revenue = revenue,
                                      attempts = attempts,
                                      impressions = impressions,
                                      clicks = clicks,
                                      fill_rate = impressions / float(attempts),
                                      ctr = clicks / float(impressions),
                                      ecpm = cost / float(impressions),
                                      app_tag = v[0].app_tag)
                                
            records.append(nsr)

        return records

class NetworkConfidential:
    pass
    
# for testing   
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.username = 'chesscom'
    nc.password = 'Y7u8i9o0'
    nc.ad_network_name = 'jumptap'
    scraper = JumpTapScraper(nc)
    print scraper.get_site_stats(date.today())
    