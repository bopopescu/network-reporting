import mechanize

from scraper import Scraper, ScraperSite

class NetworkScrapeRecord(object):
    pass

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
        self.br = mechanize.Browser()
        self.authenticate()
    
    def authenticate(self):
        self.br.open(self.LOGIN_URL)
        self.br.select_form(name = self.LOGIN_FORM_NAME)
        self.br[self.LOGIN_ACCOUNT_INPUT_NAME] = self.username
        self.br[self.LOGIN_PW_INPUT_NAME] = self.password
        response = self.br.submit()
        
        for line in response: print line
        
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

# for testing
if __name__ == '__main__':
    nc = {}
    nc['username'] = 'rawrmaan@me.com'
    nc['password'] = '606mCV&#dS'
    nc['network'] = 'iad'
    scraper = IAdScraper(nc)
    
    # iad_scraper(nc, '','')
