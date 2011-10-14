#!/usr/bin/python

import base64
import sys
import time
import traceback
import urllib2

from datetime import datetime

sys.path.append('..')
from BeautifulSoup import BeautifulSoup
from selenium import webdriver 
from pyvirtualdisplay import Display
from ad_network_reports.scrapers.network_scrape_record import NetworkScrapeRecord
from ad_network_reports.scrapers.scraper import Scraper

from datetime import date

class MillennialScraper(Scraper):

    NETWORK_NAME = 'millennial'
    SS_FNAME = 'ScraperScreen_%s.png'
    LOGIN_PAGE = 'https://developer.millennialmedia.com/Application/index.php#developerHome'
    LOGIN_TITLE = 'Monetize Mobile Apps, Mobile Advertising Platform for Developers | mmDev | Millennial Media'
    APP_STATS = ('revenue', 'ecpm', 'requests', 'impressions', 'fill_rate', 'ctr')
    MONEY_STATS = ['revenue', 'ecpm']
    PCT_STATS = ['fill_rate', 'ctr']

    def __init__(self, credentials):
        super(MillennialScraper, self).__init__(credentials)
        
        self.authenticate()

    def authenticate(self):
        # Must have selenium running or something
        self.disp = Display(visible = 0, size = (1024, 768))
        self.disp.start()
        self.browser = webdriver.Chrome('/Applications/ChromeDriver') # /usr/bin/chromedriver for EC2
        # Set max wait time to find an element on a page
        self.browser.implicitly_wait(10)
        self.browser.get(self.LOGIN_PAGE)
        
        time.sleep(1)
        self.browser.find_element_by_css_selector('.mm-button-signin').click()
        
        login = self.browser.find_element_by_css_selector('#ext-gen1029')
        login.clear()
        login.send_keys(self.username)
        pw = self.browser.find_element_by_css_selector('#ext-gen1037')
        pw.clear()
        pw.send_keys(self.password)
        self.browser.find_element_by_css_selector('#ext-gen1059').click()
        self.browser.find_element_by_css_selector('#ext-gen1080').click()
        # There are some redirects and shit that happens, chill out for a bit
        time.sleep(10)
            
        if self.browser.title == self.LOGIN_TITLE:
            raise Exception("Invalid login credentials")
        # We should now have cookies assuming things worked how I think they worked
        
    def test_login_info(self):
        """Login info has already been tested in the constructor (via the authenticate method) so we pass.
        
        Return None.
        """
        pass

    def get_ss(self):
        self.browser.get_screenshot_as_file('/home/ubuntu/' + self.SS_FNAME % time.time())

    def get_site_stats(self, start_date, end_date=None, ids=None):
        pass
        
class NetworkConfidential:
    pass
            
# for testing
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.username = 'BET'
    nc.password ='BETads'
    nc.ad_network_name = 'iad'
    scraper = MillennialScraper(nc)
    try:
        print scraper.get_site_stats(date.today())
    except:
        print traceback.print_exc() 
        pass
    scraper.browser.quit()
    scraper.disp.stop()
