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

class IAdScraper(Scraper):

    NETWORK_NAME = 'iad'
    SS_FNAME = 'ScraperScreen_%s.png'
    STATS_PAGE = 'https://iad.apple.com/itcportal/#app_homepage'
    LOGIN_TITLE = 'iTunes Connect - iAd Network Sign In'
    APPS_TITLE = 'My Apps'
    TERMS_TITLE = 'Terms of Use'
    SITE_ID_IDENTIFIER = '&siteid='
    # We have to collect the ctr in order to calculate the number of clicks
    APP_STATS = ('revenue', 'requests', 'impressions', 'ctr')
    MONEY_STATS = ['revenue']
    PCT_STATS = ['ctr']

    def __init__(self, credentials):
        super(IAdScraper, self).__init__(credentials)

        self.authenticate()

    def __del__(self):
        self.browser.quit()
        self.disp.stop()

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
            login = self.browser.find_element_by_css_selector('#accountname')
            login.clear()
            login.send_keys(self.username)
            account_password = \
                    self.browser.find_element_by_css_selector('#accountpassword')
            account_password.clear()
            account_password.send_keys(self.password)
            submit_count = 0
            exception = True
            while exception and count < 10:
                exception = False
                try:
                    self.browser.find_element_by_name('appleConnectForm').submit()
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
                    browser.title == self.APPS_TITLE)
        except Exception:
            if self.browser.title == self.LOGIN_TITLE:
                raise UnauthorizedLogin("Username or password are incorrect")
            elif self.browser.title == self.TERMS_TITLE:
                raise UnauthorizedLogin("You must agree to updated terms of use "
                        "at https://iad.apple.com/itcportal/#app_homepage")
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

    def set_dates(self, start_date, end_date):
        # Set up using custom stuff
        self.browser.find_element_by_css_selector('select'). \
                find_element_by_css_selector('option[value=customDateRange]'). \
                click()
        time.sleep(1)
        self.set_date('#gwt-debug-date-range-selector-start-date-box',
                 start_date)
        self.set_date('#gwt-debug-date-range-selector-end-date-box',
                 end_date)

    def get_cal_date(self):
        # Wait for page to load
        time.sleep(1)
        return datetime.strptime(self.browser.find_element_by_css_selector(
            'td.datePickerMonth').text, '%b %Y').date()

    def set_date(self, selector, test_date):
        # Open up the date box
        self.browser.find_element_by_css_selector(selector).click()
        time.sleep(1)
        exception = True
        count = 0
        while exception and count < 10:
            exception = False
            try:
                curr_date = self.get_cal_date()
            except selenium.common.exceptions.NoSuchElementException as \
                    exception:
                self.browser.find_element_by_css_selector(selector).click()
            count += 1
        # Which way do we go
        if curr_date > test_date:
            button = 'td>div.datePickerPreviousButton'
        else:
            button = 'td>div.datePickerNextButton'
        # GO ALL THE WAY
        while curr_date.month != test_date.month or curr_date.year != \
                test_date.year:
            self.browser.find_element_by_css_selector(button).click()
            time.sleep(1)
            curr_date = self.get_cal_date()
        time.sleep(2)
        days = self.browser.find_elements_by_css_selector('.datePickerDay')
        for day in days:
            if 'datePickerDayIsFiller' in day.get_attribute('class'):
                continue
            if day.text == str(test_date.day):
                day.click()
                break

    def get_site_stats(self, start_date):
        end_date = start_date

        # Set the dates
        self.set_dates(start_date, end_date)
        records = []

        def loaded(browser):
            """
            Return True when page has finished loading stats otherwise return
            False.
            """
            return not self.browser.find_elements_by_xpath("//img[@src=" \
                    "'https://iad.apple.com/itcportal/itcportal/ajax-loader" \
                    ".gif']")

        # Handle pagination
        nextPage = True
        while nextPage:
            # Wait for ajax
            time.sleep(1)
            WebDriverWait(self.browser, 20).until(loaded)
            # Read the page
            page = None
            while page is None:
                try:
                    page = self.browser.page_source
                except:
                    logging.error("Failed getting source")
            soup = BeautifulSoup(page)
            # Find all the apps since their TR's aren't named easily
            apps = soup.findAll('td', {'class':'td_app'})
            # Get all the tr's
            app_rows = [app.parent for app in apps]

            for row in app_rows:
                app_name =  HTMLParser.unescape.__func__(HTMLParser,
                        row.findAll('p', {"class":"app_text"})[0].text)
                app_dict = {}
                # Find desired stats
                for stat in self.APP_STATS:
                    class_name = 'td_' + stat
                    data = str(row.findAll('td', {"class":class_name})[0].text)
                    if stat in self.MONEY_STATS:
                        # Skip the dollar sign
                        data = float(filter(lambda x: x.isdigit() or x == '.',
                            data))
                    elif stat in self.PCT_STATS:
                        # Don't include the % sign
                        data = float(filter(lambda x: x.isdigit() or x == '.',
                            data))
                    else:
                        data = int(filter(lambda x: x.isdigit() or x == '.',
                            data))

                    app_dict[stat] = data

                nsr = NetworkScrapeRecord(revenue=app_dict['revenue'],
                                          attempts=app_dict['requests'],
                                          impressions=app_dict['impressions'],
                                          clicks=int(app_dict['ctr'] * app_dict[
                                              'impressions'] / 100),
                                          app_tag=app_name)
                records.append(nsr)
            # Goto the next page if it exists
            try:
                nextPage = self.browser.find_element_by_css_selector(
                        '.pagingOptionsNextPage')
            except selenium.common.exceptions.NoSuchElementException as \
                    exception:
                nextPage = False
            else:
                # Click the icon if we aren't already on the last page
                if nextPage.get_attribute('class').find('last') == -1:
                    nextPage.click()
                else:
                    nextPage = False

        return records


if __name__ == '__main__':
    NC = NetworkConfidential()
    #NC.username = 'chesscom'
    #NC.password = 'Faisal1Chess'
    #NC.username = '2_acrossair@acrossair.com'
    #NC.password = 'imano@314'
    NC.username = 'franklin@mopub.com'
    NC.password = 'MoPub512'
    NC.ad_network_name = 'iad'
    SCRAPER = IAdScraper(NC)
    print SCRAPER.get_site_stats(date(2012,4,9))

