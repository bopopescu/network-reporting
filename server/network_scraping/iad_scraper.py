<<<<<<< HEAD
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
=======
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
from network_scraping.scraper import Scraper
>>>>>>> 516b7cd7532692ffc1b32531bed6322d5dd065bd

from datetime import date
from scraper import Scraper, ScraperSite
import time

class NetworkScrapeRecord(object):
    pass

<<<<<<< HEAD
class IAdScraper(Scraper):
    
    NETWORK_NAME = 'iad'
    LOGIN_URL = 'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa'
    LOGIN_FORM_NAME = 'appleConnectForm'
    LOGIN_ACCOUNT_INPUT_NAME = 'theAccountName'
    LOGIN_PW_INPUT_NAME = 'theAccountPW'
    
    def __init__(self, credentials):
        if credentials['network'] != self.NETWORK_NAME:
            raise "Invalid credentials.  Attempting to use %s credentials for an iAd scraper" % credentials.network
        super(IAdScraper, self).__init__(credentials)
        # authenticate on creation
        self.driver = webdriver.Firefox()
        self.authenticate()
    
    def authenticate(self):
        self.driver.get(self.LOGIN_URL)
        self.driver.find_element_by_name(self.LOGIN_ACCOUNT_INPUT_NAME).send_keys(self.username)
        self.driver.find_element_by_name(self.LOGIN_PW_INPUT_NAME).send_keys(self.password)
        
        self.driver.find_elements_by_name("1.Continue")[1].click()
        
    def get_site_stats(self, start_date, end_date=None):
        if end_date is None:
            end_date = start_date
        
        self.driver.find_elements_by_link_text("iAd Network")[1].click()
        
        self.driver.implicitly_wait(30)
        # not working:
        # select_date = self.driver.find_elements_by_class_name("itc_listBox mid")
        # not sure if I can find an element by value
        # select_date.find_element_by_value("oneDay").click()
        
        # for option in select_date:
        #     if option.text == "1 Day":
        #         option.click()
        
        
        
        self.driver.find_element_by_xpath("//select/option[@value='today']").click()
        
        # have to wait for report to load before downloading it
        time.sleep(2)
        
        self.driver.find_element_by_link_text("Download Report").click()
                         
        # self.driver.find_element_by_xpath("//a[@title='download csv report']").click()
        
    def iad_scraper(network_credential, from_date, to_date):
        br = mechanize.Browser()
        br.open('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa')
        br.select_form(name='appleConnectForm')
        br['theAccountName'] = network_credential.apple_id
        br['theAccountPW'] = network_credential.password
        response = br.submit()
        #request = mechanize.Request('http://developer.apple.com/appstore/resources/iad/', ' ')
        #response = br.open(request)
        for line in response: print line

        # headers = response.readline().split(',')
        # 
        # imp_index = headers.index('Paid Impressions')
        # click_index = headers.index('Clicks')
        # net_rev_index = headers.index('Net Revenue$')
        # requests_index = headers.index('Requests')
        # cpc_index = headers.index('Net Cost Per Click')
        # app_index = headers.index('Site')
        # adunit_index = headers.index('Spot')
        # 
        # scrape_records = {}
        # for line in response:
        #     vals = line.split(',')
        #     if vals[0] != 'Totals':
        #         nsr = NetworkScrapeRecord()
        #         nsr.impressions = vals[imp_index]
        #         nsr.clicks = vals[click_index]
        #         nsr.net_revenue = vals[net_rev_index]
        #         nsr.requests = vals[requests_index]
        #         nsr.cpc = vals[cpc_index]
        #         nsr.app_name = vals[app_index]
        #         nsr.adunit_name = vals[adunit_index]
        #         scrape_records['%s||%s'%(vals[app_index],vals[adunit_index])] = nsr
        #         
        # return scrape_records
    
        # for key in scrape_records.keys():
        #     print key
        #     print scrape_records[key].impressions, ' ', scrape_records[key].clicks, ' ', scrape_records[key].net_revenue, ' ', scrape_records[key].requests, ' ', scrape_records[key].cpc, ' ', scrape_records[key].app_name, ' ', scrape_records[key].adunit_name
=======


class IAdScraper(Scraper):

    NETWORK_NAME = 'iad'
    SS_FNAME = 'ScraperScreen_%s.png'
    STATS_PAGE = 'https://iad.apple.com/itcportal/#app_homepage'
    LOGIN_TITLE = 'iTunes Connect - iAd Network Sign In'
    APP_STATS = ('revenue', 'ecpm', 'requests', 'impressions', 'fill_rate', 'ctr')
    MONEY_STATS = ['revenue', 'ecpm']
    PCT_STATS = ['fill_rate', 'ctr']

    def authenticate(self):
        # Must have selenium running or something
        self.disp = Display(visible = 0, size = (1024, 768))
        self.disp.start()
        self.browser = webdriver.Chrome()
        self.browser.get(self.STATS_PAGE)
        while self.browser.title == self.LOGIN_TITLE:
            login = self.browser.find_element_by_css_selector('#accountname')
            login.click()
            login.send_keys(self.username)
            pw = self.browser.find_element_by_name('theAccountPW')
            pw.click()
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
        time.sleep(3)

    def get_cal_date(self):
        return datetime.strptime(self.browser.find_element_by_css_selector('td.datePickerMonth').text, '%b %Y')

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

    def get_site_stats(self, start_date, end_date, ids=None):
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
        app_data = []
        for row in app_rows:
            app_name = row.findAll('p', {"class":"app_text"})[0].text
            app_dict = dict(name = app_name)
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
            app_data.append(app_dict)
        return app_data
>>>>>>> 516b7cd7532692ffc1b32531bed6322d5dd065bd

# for testing
if __name__ == '__main__':
<<<<<<< HEAD
    nc = {}
    nc['username'] = 'rawrmaan@me.com'
    nc['password'] = '606mCV&#dS'
    nc['network'] = 'iad'
    scraper = IAdScraper(nc)
    print scraper.get_site_stats(date.today())
    
    # iad_scraper(nc, '','')
=======
    nc = NetworkConfidential()
    s = datetime(2010, 10, 15)
    e = datetime(2011, 9, 15)
    nc.account = None
    nc.username = nc.apple_id ='rawrmaan@me.com'
    nc.password ='606mCV&#dS'
    nc.network = 'iad'
    iads = IAdScraper(nc)
    try:
        print iads.get_site_stats(s,e)
    except:
        print traceback.print_exc() 
        pass
    iads.browser.quit()
    iads.disp.stop()
>>>>>>> 516b7cd7532692ffc1b32531bed6322d5dd065bd
