class ServerSide(object):
  base_url = "http://www.test.com/ad?"
  def __init__(self,request,adunit=None,*args,**kwargs):
    self.request = request
    self.adunit = adunit

  def get_udid(self):
    return self.request.get('udid')

  def get_ip(self):
    return self.request.remote_addr

  def get_adunit(self):
    return self.adunit

  def get_account(self):
    return self.adunit.account
    
  def get_user_agent(self):
    return self.request.headers['User-Agent']

  @property
  def headers(self):
    return {}  

  @property  
  def payload(self):
    return None


  def bid_and_html_for_response(self,response):
    return 0.0,"<html>BLAH</html>"  