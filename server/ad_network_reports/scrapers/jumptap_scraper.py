import sys
import urllib2
import urllib

from datetime import date, timedelta
sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
#sys.path.append('/Users/tiagobandeira/Documents/mopub/server') # only needed for testing
from ad_network_reports.scrapers.scraper import Scraper, NetworkConfidential
from ad_network_reports.scrapers.network_scrape_record import \
        NetworkScrapeRecord

class JumpTapScraper(Scraper):

    NETWORK_NAME = 'jumptap'
    SITE_STAT_URL = 'https://pa.jumptap.com/pa-2.0/pub-services/v10/report.html'

    def __init__(self, credentials):
        self.adunit_publisher_ids = set(credentials.adunit_publisher_ids)
        super(JumpTapScraper, self).__init__(credentials)

    def test_login_info(self):
        """Test the username and password.

        Raise a 401 error if username or password are incorrect otherwise
        return None.
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
        adunit_index = headers.index('Spot')

        # dict stores list of nsrs for each 'spot' or ad unit where the key in
        # the dict is the app
        scrape_records = {}
        for line in response:
            vals = line.split(',')
            if vals[0] != 'Totals' and vals[adunit_index] in \
            self.adunit_publisher_ids or not self.adunit_publisher_ids:
                nsr = NetworkScrapeRecord(revenue = float(vals[revenue_index]),
                                          attempts = int(vals[request_index]),
                                          impressions = int(
                                              vals[imp_index]),
                                          clicks = int(vals[click_index]),
                                          ecpm = float(vals[cpm_index]),
                                          app_tag = vals[app_index])
                # doesn't work for a date range
                if nsr.app_tag not in scrape_records:
                    scrape_records[nsr.app_tag] = [nsr]
                else:
                    scrape_records[nsr.app_tag] += [nsr]

        records = []
        for nsr_list in scrape_records.values():
            revenue = 0
            attempts = 0
            impressions = 0
            clicks = 0
            cost = 0

            for nsr in nsr_list:
                revenue += nsr.revenue
                attempts += nsr.attempts
                impressions += nsr.impressions
                clicks += nsr.clicks
                cost += nsr.ecpm * nsr.impressions

            nsr = NetworkScrapeRecord(revenue = revenue,
                                      attempts = attempts,
                                      impressions = impressions,
                                      clicks = clicks,
                                      app_tag = nsr_list[0].app_tag)

            if attempts != 0:
                nsr.fill_rate = impressions / float(attempts) * 100
            if impressions != 0:
                nsr.ctr = clicks / float(impressions) * 100
                nsr.ecpm = cost / float(impressions)

            records.append(nsr)

        return records

if __name__ == '__main__':
    NC = NetworkConfidential()
    NC.username = 'com2ususa'
    NC.password = 'com2us1001'
    NC.adunit_publisher_ids = []
    NC.ad_network_name = 'jumptap'
    SCRAPER = JumpTapScraper(NC)
    print SCRAPER.get_site_stats(date.today() - timedelta(days = 1))
