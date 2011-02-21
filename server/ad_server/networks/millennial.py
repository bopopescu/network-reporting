from ad_server.networks.server_side import ServerSide
import urllib2
import urllib

class MillennialServerSide(ServerSide):
  base_url = "http://ads.mp.mydas.mobi/getAd.php5"
      
  def get_key_values(self):
    return {'apid':self.get_account().millenial_pub_id,
            'auid':self.get_udid(),
            'uip':self.get_ip(),
            'ua':self.get_user_agent()}
    
  def get_query_string(self):
    query_string = urllib.urlencode(self.get_key_values())       
    return query_string
  
  @property
  def url(self):
    return self.base_url + '?' + self.get_query_string()
        
  @property  
  def payload(self):
    return None
  
  # def get_user_agent(self):
  #   return "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7"
    
  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()
    
  def bid_and_html_for_response(self,response):
    # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
    if len(response.content) == 0:
      raise Exception("Millenial ad is empty")
    return 0.0,response.content
    