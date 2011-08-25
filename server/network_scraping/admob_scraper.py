import mechanize
import urllib
import json

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass

def admob_scraper(network_credential, from_date, to_date):
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1')]
    br.open('https://www.google.com/accounts/ServiceLogin?service=admob&hl=en_US&continue=https%3A%2F%2Fwww.admob.com%2Fhome%2Flogin%2Fgoogle%3F&followup=https%3A%2F%2Fwww.admob.com%2Fhome%2Flogin%2Fgoogle%3F')
    br.select_form(nr=0)
    br['Email'] = network_credential.email
    br['Passwd'] = network_credential.password
    br.submit()
    
    br.open('http://www.admob.com/reporting/sites/')
    
    request = mechanize.Request('http://www.admob.com/reporting/sites/grid', urllib.urlencode({ 'start': 0, 
                                                                                                'limit':25, 
                                                                                                'object_type':'site',
                                                                                                'ids%5B%5D':'a14970f6ad53c3c', 
                                                                                                'ids%5B%5D':'a1497a459250ea5',
                                                                                                'ids%5B%5D':'a14a6b5458b0447',
                                                                                                'ids%5B%5D':'a14a6e18d6610af',
                                                                                                'ids%5B%5D':'a14a7142acad145',
                                                                                                'ids%5B%5D':'a14a7142ee96329',
                                                                                                'ids%5B%5D':'a14a71435d8d5b3',
                                                                                                'ids%5B%5D':'a14a7143850a745',
                                                                                                'ids%5B%5D':'a14a9ed9bf1fdcd',
                                                                                                'future_ids%5B%5D':'future_sites',
                                                                                                'start_date':'2011-07-25',
                                                                                                'end_date':'2011-08-24',
                                                                                                'preset_date':'last30',
                                                                                                'name':'Last 30 Days (All Sites & Apps)',
                                                                                                'object_dimension':0,
                                                                                                'time_dimension':'day',
                                                                                                'selected_type':'cpc'}))
                                                                                                
    request.add_header("Referer", "http://www.admob.com/reporting/sites")
    request.add_header("Accept","*/*")
    request.add_header("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.3")
    request.add_header("Accept-Language", "en-US,en;q=0.8")
    request.add_header("Origin", "http://www.admob.com")
    request.add_header("X-Requested-With", "XMLHttpRequest")
    request.add_header("Connection", "keep-alive")
    
    br.set_debug_http(True)
    br.set_debug_redirects(True)
    br.set_debug_responses(True)
    
    
    response = br.open(request)
    # print response.read()

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
    nc.email ='njamal@stanford.edu'
    nc.password ='asdf!@#$'
    admob_scraper(nc, '','')