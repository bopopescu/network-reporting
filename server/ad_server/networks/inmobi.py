from ad_server.networks.server_side import ServerSide
import logging
import re
import urllib
import urllib2
import string

from xml.dom import minidom

class InMobiServerSide(ServerSide):
  base_url = "http://w.mkhoj.com/showad.asm" # live
  #base_url = "http://w.sandbox.mkhoj.com/showad.asm" # testing
  def __init__(self,request,adunit,*args,**kwargs):
    self.url_params = {}
    return super(InMobiServerSide,self).__init__(request,adunit,*args,**kwargs)
  
  @property
  def url(self):
    return self.base_url
    
  @property
  def headers(self):
    # TODO: Replace with self.get_appid()
    return {'X-Mkhoj-SiteID': '4028cb962b75ff06012b792b39b30044'}

  @property  
  def payload(self):
    # TODO: Replace with self.get_appid()
    data = {'mk-siteid': '4028cb962b75ff06012b792b39b30044',
            'mk-version': 'el-QEQE-CTATE-20090805',
            'mk-carrier': self.get_ip(),
            'h-user-agent': self.get_user_agent()}
    return urllib.urlencode(data)
    
  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()
  
  def parse_xml(self,document):
    logging.info(document)
    dom = minidom.parseString(document)
    # First see if it's a banner ad
    try:
      image_url = dom.getElementsByTagName("ImageURL")[0]  # Only use the first one
      ad_url = dom.getElementsByTagName("AdURL")[0]
      self.url_params.update(image_url=image_url,ad_url=ad_url)
    except:
      pass
    # Otherwise check if it's a text ad
    try:
      link_text = dom.getElementsByTagName("LinkText")[0]
      ad_url = dom.getElementsByTagName("AdURL")[0]
      self.url_params.update(link_text=link_text,ad_url=ad_url)
    except:
      pass

  def bid_and_html_for_response(self,response):
    if re.match("<!--.*--\>$", response.content) == None:
      # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
      self.parse_xml(response.content)
      if 'image_url' in self.url_params:
        return 0.0, banner_template.safe_substitute(self.url_params)
      elif 'link_text' in self.url_params:
        return 0.0, text_template.safe_substitute(self.url_params)

    raise Exception("InMobi ad is empty")

banner_template = string.Template("""
    <!DOCTYPE HTML>
    <html>
    <body style="margin: 0;width:320px;height:48px;padding:0;">
      <a href="$ad_url"><img src="$image_url" width=320 height=48/></a>
    </body>
    </html>""")
    
text_template = string.Template("""
    <!DOCTYPE HTML>
    <html>
    <body style="margin: 0;width:320px;height:48px;padding:0;">
    text ad
    </body>
    </html>""")
