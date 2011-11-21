import logging
import os
import sys
import urllib2
import urllib


# Paths only needed for testing
if os.path.exists('/home/ubuntu/'):
    sys.path.append('/home/ubuntu/mopub/server')
else:
    sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
from ad_network_reports.scrapers.scraper import Scraper, NetworkConfidential
from ad_network_reports.scrapers.network_scrape_record import \
        NetworkScrapeRecord
from ad_network_reports.scrapers.unauthorized_login_exception import \
        UnauthorizedLogin
from datetime import date, timedelta

class JumpTapScraper(Scraper):

    NETWORK_NAME = 'jumptap'
    SITE_STAT_URL = 'https://pa.jumptap.com/pa-2.0/pub-services/v10/report.html'

    def __init__(self, login_info):
        """Create a Jumptap scraper object.

        Take login credentials and extra info which contains a generator of app
        level publisher ids and adunit level publisher ids for the account.
        """
        if isinstance(login_info, tuple):
            credentials, self.publisher_ids, self.adunit_publisher_ids = login_info
            logging.info("JUMPTAP INFO:")
            self.publisher_ids = list(self.publisher_ids)
            self.adunit_publisher_ids = list(self.adunit_publisher_ids)
            logging.info(list(self.publisher_ids))
            logging.info(list(self.adunit_publisher_ids))
            self.adunit_publisher_ids = set(list(self.adunit_publisher_ids))
        else:
            credentials = login_info
            self.publisher_ids = ['']
            self.adunit_publisher_ids = iter([])
        super(JumpTapScraper, self).__init__(credentials)

    def test_login_info(self):
        """Test the username and password.

        Raise a 401 error if username or password are incorrect otherwise
        return None.
        """
        self.get_site_stats(date.today() - timedelta(days = 1))

    def get_site_stats(self, from_date):
        to_date = from_date

        records = []
        for publisher_id in self.publisher_ids:
            query_dict = {"user": self.username,
                          "pass": self.password,
                          "fromDate": from_date.strftime("%m/%d/%Y"),
                          "toDate": to_date.strftime("%m/%d/%Y"),
                          "sites": publisher_id,
                          "groupBy": "spot"}

            req = urllib2.Request(self.SITE_STAT_URL,
                                  urllib.urlencode(query_dict))
            try:
                response = urllib2.urlopen(req)
            except urllib2.HTTPError as e:
                if e.code in (401, 403):
                    raise UnauthorizedLogin("Invalid login for Jumptap")
                raise

            headers = response.readline().split(',')
            print headers

            revenue_index = headers.index('Net Revenue$')
            request_index = headers.index('Requests')
            imp_index = headers.index('Paid Impressions')
            click_index = headers.index('Clicks')
            ecpm_index = headers.index('Net eCPM')
            app_index = headers.index('Site')
            adunit_index = headers.index('Spot')

            revenue = 0
            attempts = 0
            impressions = 0
            clicks = 0
            cost = 0

            for line in response:
                print line
                vals = line.split(',')
                if vals[0] != 'Totals' and (vals[adunit_index] in \
                        self.adunit_publisher_ids or not
                        self.adunit_publisher_ids):
                    revenue += float(vals[revenue_index])
                    attempts += int(vals[request_index])
                    impressions += int(vals[imp_index])
                    clicks += int(vals[click_index])
                    cost += float(vals[ecpm_index]) * int(vals[imp_index])

            nsr = NetworkScrapeRecord(revenue = revenue,
                                      attempts = attempts,
                                      impressions = impressions,
                                      clicks = clicks,
                                      app_tag = publisher_id)

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
    publisher_ids = [u'pa_com2us_usa_inc__op_3d_lab_i_tes_iph_app', u'pa_com2us_usa_inc__slice_it__drd_app']
    adunit_publisher_ids = iter([u'pa_com2us_usa_inc__op_3d_lab_a_tes_drd_app_banner', u'pa_com2us_usa_inc__op_3d_lab_i_tes_iph_app_home_me_banner', u'pa_com2us_usa_inc__op_3d_lab_i_tes_iph_app_home_me_medrect', u'pa_com2us_usa_inc_slice_it_drd_app_banner', u'pa_com2us_usa_inc__slice_it__drd_app_banner2'])#iter([])
    NC.ad_network_name = 'jumptap'
    SCRAPER = JumpTapScraper((NC, publisher_ids, adunit_publisher_ids))
    print SCRAPER.get_site_stats(date.today() - timedelta(days = 1))
