import urllib2
import urllib
import time
import datetime

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass

def mobfox_scraper(network_credential, from_date, to_date):
    some_dict ={"api_key": network_credential.api_key, "publisher_id": network_credential.publisher_id, "start_date": from_date, "end_date": to_date}
    
    req = urllib2.Request('http://account.mobfox.com/reporting_api.php?'+urllib.urlencode(some_dict))
    response = urllib2.urlopen(req)

    for line in response:
        print line
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
    nc.api_key='e64d04079c63c14644fc9690a925c8af'
    nc.publisher_id='fb8b314d6e62912617e81e0f7078b47e'
    mobfox_scraper(nc, time.mktime(datetime.date(2011,8,10).timetuple()),time.mktime(datetime.date(2011,8,12).timetuple()))