from ad_server.networks.server_side import ServerSide

class MillennialServerSide(ServerSide):
  base_url = "http://ads.mp.mydas.mobi/getAd.php5"
  def __init__(self,request,app_id,*args,**kwargs):
    return super(MillennialServerSide,self).__init__(request,app_id,*args,**kwargs)
      
  def get_key_values(self):
    return {'apid':self.get_appid(),
            'auid':self.get_udid(),
            'uip':self.get_ip(),
            'ua':self.get_user_agent()}
    
  def get_query_string(self):
    import urllib
    query_string = urllib.urlencode(self.get_key_values())       
    return query_string
  
  @property
  def url(self):
    return self.base_url + '?' + self.get_query_string()
    
  def get_response(self):
    import urllib2
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()
    
  def bid_and_html_for_response(self,response):
    # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
    return 0.0,response.content
    