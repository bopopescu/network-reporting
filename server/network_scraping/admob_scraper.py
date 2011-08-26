import urllib
import urllib2
import json

#gets all sites, but would be possible to specify, not broken down by adunit.

class NetworkConfidential(object):
    pass

class NetworkScrapeRecord(object):
    pass

def admob_scraper(nc, from_date, to_date):
    req = urllib2.Request('https://api.admob.com/v2/auth/login', urllib.urlencode({'client_key': nc.client_key, 'email': nc.email, 'password': nc.password}))
    response = urllib2.urlopen(req)
    
    token = json.loads(response.readline())['data']['token']
    
    req = urllib2.Request('http://api.admob.com/v2/site/search?' + urllib.urlencode({'client_key': nc.client_key, 'token': token}))
    response = urllib2.urlopen(req)
        
    site_ids = []
    for site in json.loads(response.readline())['data']:
        site_ids.append(site['id'])

    scrape_records = {}
    for site_id in site_ids[:4]:
        req = urllib2.Request('http://api.admob.com/v2/site/stats?' + urllib.urlencode({'client_key': nc.client_key, 'token': token, 'site_id': site_id,
        'start_date': from_date, 'end_date': to_date}))
        response = urllib2.urlopen(req)

        stats = json.loads(response.readline())['data'][0]
                
        nsr = NetworkScrapeRecord()
        nsr.impressions = stats['impressions']
        nsr.clicks = stats['clicks']
        nsr.net_revenue = stats['revenue']
        nsr.requests = stats['requests']
        nsr.ecpm = stats['ecpm']
        nsr.fill_rate = stats['fill_rate']
        nsr.ctr = stats['ctr']
                
        scrape_records[site_id] = nsr
        
    return scrape_records
    
    # for key in scrape_records.keys():
    #     print key
    #     print scrape_records[key].impressions, ' ', scrape_records[key].clicks, ' ', scrape_records[key].net_revenue, ' ', scrape_records[key].requests, ' ', scrape_records[key].ecpm, ' ', scrape_records[key].fill_rate, ' ', scrape_records[key].ctr

if __name__ == '__main__':
    nc = NetworkConfidential()
    nc.email ='njamal@stanford.edu'
    nc.password ='xckjhfn3xprkxksm'
    nc.client_key = 'k907a03ee39cecb699b5ad45c5eded01'
    admob_scraper(nc, '2011-07-22','2011-07-23')