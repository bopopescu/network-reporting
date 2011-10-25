import logging
import sys
import time
import urllib2
import urllib

#sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
sys.path.append('/home/ubuntu/mopub/server')
from ad_network_reports.scrapers.network_scrape_record import \
        NetworkScrapeRecord
from ad_network_reports.scrapers.scraper import NetworkConfidential
from datetime import date, timedelta
from xml.dom import minidom

class MobFoxScraper(object):
    """One app stats returned per request sent. Can't break down by ad unit."""
    # API_KEY is MoPub specific
    API_KEY = 'MOPUB30082011'
    API_URL = 'http://account.mobfox.com/mopub_reportingapi.php?'

    def __init__(self, login_info):
        """Take tuple of login credentials and app level publisher ids.

        Only need publisher ids.
        """
        self.publisher_ids = login_info[1]

    def test_login_info(self):
        """Test publisher_ids.

        Raise an error if one of the publisher ids is incorrect otherwise
        return None.
        """
        self.get_site_stats(date.today() - timedelta(days = 1))

    def get_site_stats(self, from_date):
        to_date = from_date
        # range can't start and end on the same date for MobFox
        from_date -= timedelta(days = 1)

        req_dict ={"api_key" : self.API_KEY, "start_date" : time.mktime(
            from_date.timetuple()), "end_date" : time.mktime(to_date.
                timetuple()), "report_type" : 2}

        reports = []
        for pub_id in self.publisher_ids:
            req_dict['publisher_id'] = pub_id
            req = urllib2.Request(self.API_URL
                    + urllib.urlencode(req_dict))

            response = urllib2.urlopen(req)
            line = response.read()
            if line.find("error") != -1:
                raise Exception(line)
            self.dom = minidom.parseString(line)

            try:
                nsr = NetworkScrapeRecord(revenue = float(self.get_value(
                    "earnings")),
                    # We can't get the number of attempts / requests
                    attempts = 0,
                    impressions = int(self.get_value("impressions")),
                    # We can't get this and we don't have # attempts so we can't
                    # calculate it
                    fill_rate = 0.0,
                    clicks = int(self.get_value("clicks")),
                    ecpm = float(self.get_value("ecpm")),
                    ctr = float(self.get_value("ctr")),
                    app_tag = pub_id)
                reports.append(nsr)
            except Exception:
                logging.error("Day range (%s to %s) selected for mobfox "
                        "doesn\'t have any data" %
                        (from_date.strftime("%Y %m %d"), to_date.
                            strftime("%Y %m %d")))
                raise

        return reports

    def get_value(self, name):
        nodes = self.dom.getElementsByTagName(name)[0].childNodes
        if nodes:
            return nodes[0].nodeValue
        else:
            return 0

if __name__ == '__main__':
    NC = NetworkConfidential()
    publisher_ids = ['ddcc935d2bc034b2823e04b24ff544a9',
            'e884e3c21a498d57f7d1cb1400c5ab9b']
    SCRAPER = MobFoxScraper((NC, publisher_ids))
    print SCRAPER.get_site_stats(date.today() - timedelta(days=1))
