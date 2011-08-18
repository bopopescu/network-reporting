import urllib2
import urllib
class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass

def jumptap_scraper(network_credential, from_date, to_date):
    some_dict ={"user": network_credential.username, "pass": network_credential.password, "fromDate": from_date, "toDate": to_date, "groupBy": "spot"}
    
    if network_credential.app_name:
        some_dict['sites'] = network_credential.app_name
    
    req = urllib2.Request('https://pa.jumptap.com/pa-2.0/pub-services/v10/report.html?'+urllib.urlencode(some_dict))
    response = urllib2.urlopen(req)
    
    headers = response.readline().split(',')
    
    imp_index = headers.index('Paid Impressions')
    click_index = headers.index('Clicks')
    net_rev_index = headers.index('Net Revenue$')
    requests_index = headers.index('Requests')
    cpc_index = headers.index('Net Cost Per Click')
    app_index = headers.index('Site')
    adunit_index = headers.index('Spot')
    
    scrape_records = {}
    for line in response:
        vals = line.split(',')
        if vals[0] != 'Totals':
            nsr = NetworkScrapeRecord()
            nsr.impressions = vals[imp_index]
            nsr.clicks = vals[click_index]
            nsr.net_revenue = vals[net_rev_index]
            nsr.requests = vals[requests_index]
            nsr.cpc = vals[cpc_index]
            nsr.app_name = vals[app_index]
            nsr.adunit_name = vals[adunit_index]
            scrape_records['%s||%s'%(vals[app_index],vals[adunit_index])] = nsr
            
    # return scrape_records
    for key in scrape_records.keys():
        print key
        print scrape_records[key].impressions, ' ', scrape_records[key].clicks, ' ', scrape_records[key].net_revenue, ' ', scrape_records[key].requests, ' ', scrape_records[key].cpc, ' ', scrape_records[key].app_name, ' ', scrape_records[key].adunit_name
    
if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.username='vrubba'
    nc.password='fluik123!'
    nc.app_name=None
    #nc.app_name='pa_fluik_entertain_office_jerk_fre_drd_app'
    jumptap_scraper(nc, '7/1/2011','7/1/2011')
    
