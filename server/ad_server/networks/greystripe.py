from ad_server.networks.server_side import ServerSide
import urllib
import urllib2

class GreyStripeServerSide(ServerSide):
  base_url = "http://adsx.greystripe.com/openx/www/delivery/mw2.php"
  @property
  def url(self):
    return self.base_url
    
  @property
  def headers(self):
    # TODO: Replace with self.get_appid()
    return {'User-Agent': self.request.headers['User-Agent']}

  @property  
  def payload(self):
    # TODO: Replace with self.get_appid()
    ignore_headers = ["PRAGMA","CACHE-CONTROL","CONNECTION","USER-AGENT","COOKIE"]
    
    phone_headers = {}
    for header in self.request.headers:
      if not header.upper() in ignore_headers:
        phone_headers[header] = self.request.headers[header]
    
    phone_headers = [urllib.urlencode({key.upper():value}) for key,value in phone_headers.iteritems()]    
    size = self.adunit.format if "full" not in self.adunit.format else '300x250'


    data = {'language':'python',
            'version':'1.0',
            'format':'html',
            'ip': self.get_ip(),
            'site_id': self.get_account().greystripe_pub_id, 
            'sizes':size, #TODO: have this be an input parameter
            }
    return urllib.urlencode(data)+'&phone_headers='+'||'.join(phone_headers)
    
  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()
    
  def bid_and_html_for_response(self,response):
    if len(response.content) == 0 or \
      response.status_code != 200:
        raise Exception("GreyStripe ad is empty")

    return 0.0,response.content
