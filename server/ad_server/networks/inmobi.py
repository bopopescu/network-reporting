from ad_server.networks.server_side import ServerSide
import logging
import re
import urllib
import urllib2

class InMobiServerSide(ServerSide):
  base_url = "http://w.mkhoj.com/showad.asm"
  def __init__(self,request,app_id,*args,**kwargs):
    return super(InMobiServerSide,self).__init__(request,app_id,*args,**kwargs)
  
  @property
  def url(self):
    return self.base_url
    
  @property
  def headers(self):
    # TODO: Replace with self.get_appid()
    return {'X-mKhoj-SiteId': '4028cb962b75ff06012b792b39b30044'}

  @property  
  def payload(self):
    # TODO: Replace with self.get_appid()
    data = {'mk-siteid': '4028cb962b75ff06012b792b39b30044',
            'mk-version': 'el-QEQE-CTATE-20090805',
            # TODO: Replace with self.get_ip()
            'mk-carrier': '208.54.5.79',
            'h-user-agent': self.get_user_agent()}
    return urllib.urlencode(data)
    
  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()
    
  def bid_and_html_for_response(self,response):
    if re.match("<!--.*--\>$", response.content) == None:
      # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
      return 0.0,response.content
    else:
      raise Exception("InMobi ad is empty")
    