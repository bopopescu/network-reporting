import json
import logging
import os
import sys
import urllib2

# Paths only needed for testing
if os.path.exists('/home/ubuntu/'):
    sys.path.append('/home/ubuntu/mopub/server')
else:
    # Assumes it is being called from the server dir
    sys.path.append(os.environ['PWD'])
from ad_network_reports.scrapers.network_scrape_record import \
        NetworkScrapeRecord
from ad_network_reports.scrapers.scraper import Scraper, NetworkConfidential
from ad_network_reports.scrapers.unauthorized_login_exception import \
        UnauthorizedLogin
from datetime import datetime, date, timedelta
from hashlib import sha1
from hmac import new as hmac

class InMobiScraper(Scraper):

    NETWORK_NAME = 'inmobi'
    API_URL = 'http://publisherapi.inmobi.com'
    SITE_STAT_URL = '/pubData-1.0/extern/reports/%(username)s/ad-view/all/%' \
            '(platform)s/publisher.json?fromDate=%(start_date)s&toDate=%' \
            '(end_date)s&filter=site'
    # TIMEZONE is included in DATE_FMT
    DATE_FMT = '%a, %d %b %Y %H:%M:%S PDT'
    PLATFORM = 'all'

    def test_login_info(self):
        """Test the Access ID and Secret Key.

        Raise a 403 error if Access ID or Secret Key are incorrect otherwise
        return None.
        """
        self.get_site_stats(date.today() - timedelta(days = 1))

    def get_site_stats(self, start_date):
        # Date can't be today
        end_date = start_date

        start_str = start_date.strftime('%d%b%Y').lower()
        end_str = end_date.strftime('%d%b%Y').lower()
        auth_dict = dict(username = self.username, platform = self.PLATFORM,
                start_date = start_str, end_date = end_str)
        url = self.SITE_STAT_URL % auth_dict
        now = datetime.now().strftime(self.DATE_FMT)
        full_url = self.API_URL + url

        final_str = 'GET\n%s\n%s' % (now, url)

        # Strings are stored as unicode in appengine
        self.password = str(self.password)
        encoded_url = hmac(self.password, final_str, sha1).digest().encode(
                'base64')[:-1]

        req = urllib2.Request(full_url)
        req.add_header('Authorization', 'Inmobi WS token :%s' % encoded_url)
        req.add_header('Date', now)
        req.add_header('x-data-user', self.username)

        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            if e.code in (401, 403):
                raise UnauthorizedLogin("Invalid login for InMobi")
            raise

        line = response.read()
        if line.find('error') != -1:
            logging.error("Day range (%s to %s) selected for InMobi doesn\'t "
                    "have any data. %s" % (start_date.strftime("%Y %m %d"),
                        end_date.strftime("%Y %m %d"), line))
            # InMobi Error's when there is no data to show ie other networks
            # return 0's so in this case we will just return an nsr with 0's
            return [NetworkScrapeRecord()]
#            raise InMobiError(line[line.find('<error>') + len('<error>') :
#                line.find('</error>')])

        dictionary = json.loads(line)

        reports_dicts = dictionary['data']['reports']
        reports = []
        for report_dict in reports_dicts:
            nsr = NetworkScrapeRecord(revenue=float(report_dict['earn']),
                    attempts=int(report_dict['req']),
                    impressions=int(report_dict['imp']),
                    clicks=int(report_dict['clk']),
                    app_tag=str(report_dict['excol']))
            reports.append(nsr)

        return reports

class InMobiError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

if __name__ == '__main__':
    NC = NetworkConfidential()
    # access_id
    NC.username = '4028cb972fe21753012ffb7680350267'
    # secret_key
    NC.password = '0588884947763'
    NC.ad_network_name = 'inmobi'
    SCRAPER = InMobiScraper(NC)
    print SCRAPER.get_site_stats(date.today() - timedelta(days=1))
