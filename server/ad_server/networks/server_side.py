class ServerSide(object):
  base_url = "http://www.test.com/ad?"
  def __init__(self,request,app_id=None,*args,**kwargs):
    self.request = request
    self.app_id = app_id

  def get_udid(self):
    return self.request.get('udid')

  def get_ip(self):
    return self.request.remote_addr

  def get_appid(self):
    return self.app_id
    
  def get_user_agent(self):
    return self.request.headers['User-Agent']

  @property
  def headers(self):
    return {}  

  def bid_and_html_for_response(self,response):
    return 0.0,"<html>BLAH</html>"  
  