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
from network_scraping.network_scrape_record import NetworkScrapeRecord
from network_scraping.scraper import Scraper

from datetime import date

class IAdScraper(Scraper):

    NETWORK_NAME = 'iad'
    SS_FNAME = 'ScraperScreen_%s.png'
    STATS_PAGE = 'https://iad.apple.com/itcportal/#app_homepage'
    LOGIN_TITLE = 'iTunes Connect - iAd Network Sign In'
    APP_STATS = ('revenue', 'ecpm', 'requests', 'impressions', 'fill_rate', 'ctr')
    MONEY_STATS = ['revenue', 'ecpm']
    PCT_STATS = ['fill_rate', 'ctr']

    def __init__(self, credentials):
        super(IAdScraper, self).__init__(credentials)
        
        self.authenticate()

    def authenticate(self):
        # Must have selenium running or something
        self.disp = Display(visible = 0, size = (1024, 768))
        self.disp.start()
        self.browser = webdriver.Chrome('/Applications/ChromeDriver')
        # Set max wait time to find an element on a page
        self.browser.implicitly_wait(10)
        self.browser.get(self.STATS_PAGE)
        while self.browser.title == self.LOGIN_TITLE:
            login = self.browser.find_element_by_css_selector('#accountname')
            login.click()
            login.clear()
            login.send_keys(self.username)
            pw = self.browser.find_element_by_name('theAccountPW')
            pw.click()
            pw.clear()
            pw.send_keys(self.password)
            self.browser.find_element_by_name('appleConnectForm').submit()
            # There are some redirects and shit that happens, chill out for a bit
            time.sleep(10)
        # We should now have cookies assuming things worked how I think they worked

    def get_ss(self):
        self.browser.get_screenshot_as_file('/home/ubuntu/' + self.SS_FNAME % time.time())

    def set_dates(self, start_date, end_date):
        # Set up using custom stuff
        self.browser.find_element_by_css_selector('select').find_element_by_css_selector('option[value=customDateRange]').click()
        self.set_date('#gwt-debug-date-range-selector-start-date-box', start_date)
        self.set_date('#gwt-debug-date-range-selector-end-date-box', end_date)

    def get_cal_date(self):
        # Wait for page to load
        time.sleep(3)
        return datetime.strptime(self.browser.find_element_by_css_selector('td.datePickerMonth').text, '%b %Y').date()

    def set_date(self, selector, date):
        # Open up the date box
        self.browser.find_element_by_css_selector(selector).click()
        curr_date = self.get_cal_date()
        # Which way do we go
        if curr_date > date:
            button = 'td>div.datePickerPreviousButton'
        else:
            button = 'td>div.datePickerNextButton'
        #b2 = button + ' input'
        # GO ALL THE WAY
        while curr_date.month != date.month or curr_date.year != date.year:
            self.browser.find_element_by_css_selector(button).click()
            #self.selenium.mouse_over(button)
            #self.selenium.mouse_down(button)
            #self.selenium.mouse_up(button)
            curr_date = self.get_cal_date()
            #self.selenium.click(b2)
        days = self.browser.find_elements_by_css_selector('.datePickerDay')
        for day in days:
            if 'datePickDayIsFiller' in day.get_attribute('class'):
                continue
            if day.text == str(date.day):
                day.click()
                break

    def get_site_stats(self, start_date, end_date=None, ids=None):
        if end_date is None:
            end_date = start_date
        
        # Set the dates
        self.set_dates(start_date, end_date)
        # read the shit
        page = None
        while page is None:
            try:
                page = self.browser.page_source
            except:
                print "failed getting source"
        soup = BeautifulSoup(page)
        # Find all the apps since their TR's aren't named easily
        apps = soup.findAll('td',{'class':'td_app'})
        # Get all the tr's
        app_rows = [app.parent for app in apps]
        records = []
        for row in app_rows:
            app_name = row.findAll('p', {"class":"app_text"})[0].text
            app_dict = dict(apple_id = app_name[app_name.find(' ') + 1:])
            # Find desired stats
            for stat in self.APP_STATS:
                class_name = 'td_' + stat
                data = str(row.findAll('td',{"class":class_name})[0].text)
                if stat in self.MONEY_STATS:
                    # Skip the dollar sign
                    # TODO probably need to do multi-country support because 
                    # pound signs and stuff are after the number not before like
                    # the dollar sign
                    data = eval(data[1:])
                elif stat in self.PCT_STATS:
                    # Don't include the % sign
                    data = eval(data[:-1])
                else:
                    data = eval(data)
                app_dict[stat] = data
                
            nsr = NetworkScrapeRecord(revenue = app_dict['revenue'],
                                      attempts = app_dict['requests'],
                                      impressions = app_dict['impressions'],
                                      fill_rate = app_dict['fill_rate'],
                                      clicks = int(app_dict['ctr'] * app_dict['impressions']),
                                      ctr = app_dict['ctr'],
                                      ecpm = app_dict['ecpm'],
                                      app_tag = app_dict['apple_id'])
            records.append(nsr)
        return records

# [{'fill_rate': 0.0, 'name': u'AppleID: 362641118', 'ctr': 0.0, 'revenue': 0.0, 'ecpm': 0.0, 'impressions': '0', 'requests': '0'}]
class NetworkConfidential:
    pass
            
# for testing
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.username = 'rawrmaan@me.com'
    nc.password ='606mCV&#dS'
    nc.ad_network_name = 'iad'
    scraper = IAdScraper(nc)
    try:
        print scraper.get_site_stats(date.today())
    except:
        print traceback.print_exc() 
        pass
    scraper.browser.quit()
    scraper.disp.stop()
