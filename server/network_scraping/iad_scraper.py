import mechanize

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass

def iad_scraper(network_credential, from_date, to_date):
    br = mechanize.Browser()
    br.open('http://developer.apple.com/appstore/resources/iad/')
    br.select_form(name='appleConnectForm')
    br['theAccountName'] = network_credential.apple_id
    br['theAccountPW'] = network_credential.password
    br.submit()
    request = mechanize.Request('http://developer.apple.com/appstore/resources/iad/', ' ')
    br.open(request)

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
    nc.apple_id ='rawrmaan@me.com'
    nc.password ='606mCV&#dS'
    iad_scraper(nc, time.mktime(datetime.date(2011,8,10).timetuple()),time.mktime(datetime.date(2011,8,11).timetuple()))