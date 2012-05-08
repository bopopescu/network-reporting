import selenium
import os
import sys
import time
import logging

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
from common.utils.BeautifulSoup import BeautifulSoup
from datetime import date, datetime, timedelta
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from HTMLParser import HTMLParser

class MillennialScraper(Scraper):

    NETWORK_NAME = 'millennial'
    STATS_PAGE = 'https://developer.millennialmedia.com/Application/index.php' \
            '?env=prod&default=login#login'
    LOGIN_TITLE = 'Sign-In, Log-in to Your Account | mmDev | Millennial Media'
    DASHBOARD_TITLE = 'Dashboard | Millennial Media'
    # We have to collect the ctr in order to calculate the number of clicks
    APP_STATS = ('requests', 'views', 'clicks', 'earnings')
    MONEY_STATS = ('revenue')

    def __init__(self, credentials):
        super(MillennialScraper, self).__init__(credentials)

        self.authenticate()

    def __del__(self):
        #self.browser.quit()
        #self.disp.stop()
        pass

    def authenticate(self):
        self.disp = Display(visible = 0, size = (1024, 768))
        self.disp.start()
        self.browser = webdriver.Chrome('/usr/bin/chromedriver')
        # Set max wait time to find an element on a page
        self.browser.implicitly_wait(10)
        self.browser.get(self.STATS_PAGE)

        time.sleep(1)
        count = 0
        while self.browser.title == self.LOGIN_TITLE and count < 2:
            login = self.browser.find_element_by_css_selector('#ext-gen1037')
            login.clear()
            login.send_keys(self.username)
            account_password = \
                    self.browser.find_element_by_css_selector('#ext-gen1049')
            account_password.clear()
            account_password.send_keys(self.password)
            submit_count = 0
            exception = True
            while exception and count < 10:
                exception = False
                try:
                    self.browser.find_element_by_css_selector(
                            '#ext-gen1062').click()
                except selenium.common.exceptions.NoSuchElementException as \
                        exception:
                    pass
                submit_count += 1
            # There are some redirects and shit that happens, chill out for a bit
            time.sleep(3)
            count += 1


        try:
            # we have to wait for the page to refresh, the last thing that
            # seems to be updated is the title
            WebDriverWait(self.browser, 15).until(lambda browser :
                    browser.title == self.DASHBOARD_TITLE)
        except Exception:
            print 'Title:'
            print self.browser.title
            if self.browser.title == self.LOGIN_TITLE:
                raise UnauthorizedLogin("Username or password are incorrect")
            else:
                raise

        # We should now have cookies

    def test_login_info(self):
        """Login info has already been tested in the constructor (via the
        authenticate method) so we pass.

        Return None.
        """
        pass

    def get_ss(self):
        self.browser.get_screenshot_as_file('/home/ubuntu/' + self.SS_FNAME %
                time.time())

    def get_site_stats(self, day):
        """
        Note: can't get elements by id because the ids change
        """
        # Set the dates
        inputs = self.browser.find_elements_by_css_selector('input')
        for date_input in inputs[:2]:
            date_input.clear()
            date_input.send_keys(day.strftime('%m/%d/%Y'))

        records = []

        def loaded(browser):
            """
            Return True when page has finished loading stats otherwise return
            False.
            """
            return not self.browser.find_element_by_css_selector("#ext-gen1677")

        # Handle pagination
        page_number = 1
        next_page = True
        while next_page:
            # Wait for ajax
            time.sleep(1)
            #WebDriverWait(self.browser, 20).until(loaded)
            # Read the page
            page = None
            while page is None:
                try:
                    page = self.browser.page_source
                except:
                    logging.error("Failed getting source")
            soup = BeautifulSoup(page)
            app_rows = soup.findAll('tr', {'class':'x-grid-row'})
            print app_rows

            for row in app_rows:
                app_name =  HTMLParser.unescape.__func__(HTMLParser,
                        row.findAll('td', {"class": "app-table-name"})[0].text)
                app_dict = {}
                # Find desired stats
                for stat in self.APP_STATS:
                    class_name = 'app-table-' + stat
                    data = str(row.findAll('td', {"class":class_name})[0].text)
                    if stat in self.MONEY_STATS:
                        # Skip the dollar sign
                        data = float(filter(lambda x: x.isdigit() or x == '.',
                            data))
                    else:
                        data = int(filter(lambda x: x.isdigit() or x == '.',
                            data))

                    app_dict[stat] = data

                nsr = NetworkScrapeRecord(revenue=app_dict['earnings'],
                                          attempts=app_dict['requests'],
                                          impressions=app_dict['views'],
                                          clicks=app_dict['clicks'],
                                          app_tag=app_name)
                records.append(nsr)
            # Goto the next page if it exists
            try:
                page_input = self.browser.find_element_by_css_selector(
                        '#ext-gen1239')
            except selenium.common.exceptions.NoSuchElementException as \
                    exception:
                next_page = False
            else:
                # Click the icon if we aren't already on the last page
                if page_number not in self.browser. \
                        find_element_by_css_selector('#tbtext-1058').text:
                    page_number += 1
                    page_input.clear()
                    page_input.send_keys(page_number)
                else:
                    next_page = False

        return records


if __name__ == '__main__':
    NC = NetworkConfidential()
    NC.username = 'michael@pocketgems.com'
    NC.password = 'pocketgems123'
    NC.ad_network_name = 'millennial'
    SCRAPER = MillennialScraper(NC)
    print SCRAPER.get_site_stats(date(2012,4,9))

