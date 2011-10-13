import json
from utils.decorators import web_dec
import tornado.web

from network_scraping.ad_networks import ad_networks
from network_scraping.models import AdNetworkLoginInfo

class StatsHandler(tornado.web.RequestHandler):
    @web_dec
    def post(self):
        ad_network_name = self.request.POST['ad_network_name']
        username = self.request.POST['username']
        password = self.request.POST['password']
        client_key = self.request.POST['client_key']
        send_mail = self.request.POST['send_mail']
        
        login_info = AdNetworkLoginInfo(account = self.account,
                                        ad_network_name = ad_network_name,
                                        username = username,
                                        password = password,
                                        client_key = client_key,
                                        publisher_ids = publisher_ids)
        
        results = {}
	    try:
            scraper = ad_networks[login_info.ad_network_name].constructor(login_info)
            scraper.test_login_info()
        except Exception:
            results = {'status' : 400}
        else:
            results = {'status' : 200}
        self.write(json.dumps(results))
        
        
