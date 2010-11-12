from ad_server.networks.server_side import ServerSide
import logging
import re
import urllib2
import string

class BrightRollServerSide(ServerSide):
  base_url = "http://mobile.btrll.com/adwhirl/req/?adFeedKey=506"
  def __init__(self,request,app_id,*args,**kwargs):
    return super(BrightRollServerSide,self).__init__(request,app_id,*args,**kwargs)
  
  @property
  def url(self):
    return self.base_url
    
  @property
  def headers(self):
    # TODO: Replace with self.get_appid()
    return {}

  @property  
  def payload(self):
    return None
    
  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()
    
  def bid_and_html_for_response(self,response):
    return 0.0,string.replace(response.content,"<head>","<head><script type=\"text/javascript\">\nwindow.addEventListener(\"load\", function() { window.location=\"mopub://finishLoad\";}, false);function webviewDidAppear(){playAdVideo();}\n</script>",1)
    #return 0.0,string.replace(response.content,"<head>","<head><script type=\"text/javascript\">\nwindow.addEventListener(\"load\", function() { loadAdVideo();playAdVideo();}, false);function webviewDidAppear(){playAdVideo();}\n</script>",1)
    #return 0.0, "<html><body>hi</body></html>"
    #return 0.0,response.content
    