import sys
sys.path.append('/home/ubuntu/mopub_experimental/server')

import json
from utils.decorators import web_dec
import tornado.web

from network_scraping.ad_networks import ad_networks
from network_scraping.models import AdNetworkLoginInfo

class CheckLoginCredentialsHandler(tornado.web.RequestHandler):
    @web_dec
    def post(self):
        ad_network_name = self.get_argument('ad_network_name')
        username = self.get_argument('username')
        password = self.get_argument('password')
        client_key = self.get_argument('client_key')
        send_mail = self.get_argument('send_mail') == 'True'
        
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
        
        
