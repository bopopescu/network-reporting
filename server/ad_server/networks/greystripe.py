from ad_server.networks.server_side import ServerSide
import logging
import re
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
      
          
    data = {'language':'python',
            'version':'1.0',
            'format':'html',
            'ip': self.get_ip(),
            'site_id':"10641", #TODO: allow input of site id
            'sizes':"320x48", #TODO: have this be an input parameter
            }
    return urllib.urlencode(data)+'&phone_headers='+'||'.join(phone_headers)
    
  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()
    
  def bid_and_html_for_response(self,response):
    if re.match("<!--.*--\>$", response.content) == None:
      # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
      return 0.0,response.content
    else:
      raise Exception("GreyStripe ad is empty")