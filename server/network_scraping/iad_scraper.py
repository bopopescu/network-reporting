import mechanize
import urllib2
import time
import sys

from datetime import datetime

sys.path.append('..')
from BeautifulSoup import BeautifulSoup
from selenium import selenium
from network_scraping.scraper import Scraper

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass



class IAdScraper(Scraper):

    NETWORK_NAME = 'iad'
    STATS_PAGE = 'https://iad.apple.com/itcportal/#app_homepage'
    APP_STATS = ('revenue', 'ecpm', 'requests', 'impressions', 'fill_rate', 'ctr')
    MONEY_STATS = ['revenue', 'ecpm']
    PCT_STATS = ['fill_rate', 'ctr']

    def authenticate(self):
        # Must have selenium running or something
        self.selenium = selenium('localhost', 4444, '*chrome', self.STATS_PAGE)
        self.selenium.start()
        self.selenium.open(self.STATS_PAGE)
        self.selenium.type('name=theAccountName', self.username)
        self.selenium.type('name=theAccountPW', self.password)
        self.selenium.click('name=1.Continue')
        # There are some redirects and shit that happens, chill out for a bit
        time.sleep(3)
        # We should now have cookies assuming things worked how I think they worked

    def set_dates(self, start_date, end_date):
        # Set up using custom stuff
        self.selenium.select('css=select', 'value=customDateRange')
        self.set_date('css=#gwt-debug-date-range-selector-start-date-box', start_date)
        self.set_date('css=#gwt-debug-date-range-selector-end-date-box', end_date)
        time.sleep(8)

    def get_cal_date(self):
        return datetime.strptime(self.selenium.get_text('css=td.datePickerMonth'), '%b %Y')

    def set_date(self, selector, date):
        # Open up the date box
        self.selenium.click(selector)
        curr_month = self.get_cal_date()
        # Which way do we go
        if curr_month > date:
            button = 'css=td>div.datePickerPreviousButton-up'
        else:
            button = 'css=td>div.datePickerNextButton-up'
        #b2 = button + ' input'
        # GO ALL THE WAY
        while self.get_cal_date().month != date.month:
            self.selenium.mouse_down(button)
            self.selenium.mouse_up(button+'-hovering')
            #self.selenium.click(b2)
        sel1 = 'css=td[class="datePickerDay "]:contains("^%s$")'
        sel2 = 'css=td[class="datePickerDay datePickerDayIsWeekend "]:contains("^%s$")'
        sel3 = 'css=td[class="datePickerDay datePickerDayIsToday "]:contains("^%s$")'
        sel4 = 'css=td[class="datePickerDay datePickerDayIsWeekend datePickerDayIsToday "]:contains("^%s$")'
        sels = [sel1,sel2,sel3,sel4]
        sels = [sel % date.day for sel in sels]
        for sel in sels:
            try:
                self.selenium.click(sel)
                return
            except Exception, e:
                pass

    def get_site_stats(self, start_date, end_date, ids=None):
        # Set the dates
        self.set_dates(start_date, end_date)

        # read the shit
        page = self.selenium.get_html_source()
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

if __name__ == '__main__':
    nc = NetworkConfidential()
    s = datetime(2011, 7, 15)
    e = datetime(2011, 9, 15)
    nc.account = None
    nc.username = nc.apple_id ='rawrmaan@me.com'
    nc.password ='606mCV&#dS'
    nc.network = 'iad'
    iads = IAdScraper(nc)
    try:
        print iads.get_site_stats(s,e)
    except:
        pass
    iads.selenium.stop()
