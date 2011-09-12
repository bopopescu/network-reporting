import mechanize
import urllib2
import time
import sys

sys.path.append('..')
from BeautifulSoup import BeautifulSoup
from network_scraping.scraper import Scraper

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass



class IAdScraper(Scraper):

    NETWORK_NAME = 'iad'
    STATS_PAGE = 'https://iad.apple.com/itcportal/#app_homepage'
    APP_STATS = ('revenune', 'ecpm', 'requests', 'impressions', 'fill_rate', 'ctr')
    MONEY_STATS = ['revenue', 'ecpm']
    PCT_STATS = ['fill_rate', 'ctr']

    def authenticate(self):
        self.browser.open(self.STATS_PAGE)
        self.browser.select_form(name='appleConnectForm')
        self.browser['theAccountName'] = self.username
        self.browser['theAccountPW'] = self.password
        self.browser.submit()

        # We should now have cookies assuming things worked how I think they worked


    def get_site_stats(self, start_date, end_date, ids=None):
        self.browser.open(self.STATS_PAGE)
        page = self.browser.response().read()
        print page
        soup = BeautifulSoup(page)
        # Find all the apps since their TR's aren't named easily
        apps = soup.findAll({'class':'td_app'})
        # Get all the tr's
        app_rows = [app.parent for app in apps]
        app_data = []
        for row in app_rows:
            app_name = row.findAll(p, {"class":"app_text"})
            app_dict = dict(name = app_name)
            # Find desired stats
            for stat in self.APP_STATS:
                class_name = 'td_' + stat
                data = row.findAll({"class":class_name})[0].contents
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




def iad_scraper(network_credential, from_date, to_date):
    br = mechanize.Browser()
    br.open('http://developer.apple.com/appstore/resources/iad/')
    br.select_form(name='appleConnectForm')
    br['theAccountName'] = network_credential.apple_id
    br['theAccountPW'] = network_credential.password
    br.submit()
    request = mechanize.Request('http://developer.apple.com/appstore/resources/iad/', ' ')
    response = br.open(request)
    #for line in response: print line

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

if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.account = None
    nc.username = nc.apple_id ='rawrmaan@me.com'
    nc.password ='606mCV&#dS'
    nc.network = 'iad'
    iads = IAdScraper(nc)
    iad_scraper(nc,'','')
    print iads.get_site_stats(None,None)
