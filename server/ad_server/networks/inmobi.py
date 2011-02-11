from ad_server.networks.server_side import ServerSide
import logging
import re
import urllib
import urllib2
import string

from xml.dom import minidom

class InMobiServerSide(ServerSide):
  base_url = "http://w.inmobi.com/showad.asm" # live
  def __init__(self,request,adunit,*args,**kwargs):
    self.url_params = {}
    return super(InMobiServerSide,self).__init__(request,adunit,*args,**kwargs)

  @property
  def url(self):
    return self.base_url

  @property
  def headers(self):
    # TODO: Replace with self.get_appid()
    return {'X-Mkhoj-SiteID': '4028cb962b75ff06012b792fc5fb0045',
            'X-InMobi-Phone-UserAgent': self.get_user_agent() }

  @property  
  def payload(self):
    # TODO: Replace with self.get_appid()
    data = {'mk-siteid': '4028cb962b75ff06012b792fc5fb0045',
            'mk-version': 'pr-SPEC-ATATA-20090521',
            'mk-ad-slot': '9',
            'u-id': self.get_udid(),
            #'mk-carrier': self.get_ip(),
            'mk-carrier': '208.54.5.50',
            #'h-user-agent': self.get_user_agent()}
            'h-user-agent': 'InMobi_AndroidSDK%3D1.1%20(Specs)'}
    return urllib.urlencode(data)

  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)
    return response.read()

  def _getText(self,node):
      return node.childNodes[0].data

  def parse_xml(self,document):
    logging.info(document)
    try:
      dom = minidom.parseString(document)
    except:
      pass
    # First see if it's a banner ad
    try:
      image_url = self._getText(dom.getElementsByTagName("ImageURL")[0])  # Only use the first one
      ad_url = self._getText(dom.getElementsByTagName("AdURL")[0])
      self.url_params.update(image_url=image_url,ad_url=ad_url)
    except:
      pass
    # Otherwise check if it's a text ad
    try:
      link_text = self._getText(dom.getElementsByTagName("LinkText")[0])
      ad_url = self._getText(dom.getElementsByTagName("AdURL")[0])
      self.url_params.update(link_text=link_text,ad_url=ad_url)
    except:
      pass

  def bid_and_html_for_response(self,response):
    # Test responses
    # response.content = '<AdResponse><Ads number="1"><Ad type="banner" actionType="android"><ImageURL>http://r.w.inmobi.com/FileData/513cc422-33a6-4274-9e22-dd12e84e23d14.png</ImageURL><ImageAltText></ImageAltText><Placement>page</Placement><AdURL>http://c.w.mkhoj.com/c.asm/3/t/c7i/pl5/2/2m/aj/u/0/0/1/354957037659003/11ba085a-012e-1000-d9a8-00020fe80003/1/829a0c01</AdURL></Ad></Ads></AdResponse>'
    # response.content = '<AdResponse><Ads number="1"><Ad type="text" actionType="web"><LinkText>Sick of being overweight? Get Free Guide</LinkText><Placement>page</Placement><AdURL>http://c.w.mkhoj.com/c.asm/3/t/c7i/pl5/2/2m/aj/u/0/0/1/354957037659003/1217ae48-012e-1000-de75-00020ff10003/1/9c3e6541</AdURL></Ad></Ads></AdResponse>'
    logging.info(response.content)
    if re.match("^<!--.*--\>$", response.content) == None:
      # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
      self.parse_xml(response.content)
      if 'image_url' in self.url_params:
        return 0.0, banner_template.safe_substitute(self.url_params)
      elif 'link_text' in self.url_params:
        return 0.0, text_template.safe_substitute(self.url_params)

    raise Exception("InMobi ad is empty")

banner_template = string.Template(
"""<!DOCTYPE HTML>
<html>
<body style="margin:0;width:320px;height:48px;padding:0;">
  <a href="$ad_url"><img src="$image_url" width=320 height=48/></a>
</body>
</html>""")

text_template = string.Template(
"""<!DOCTYPE HTML>
<html>
<body style="margin:0;width:320px;height:50px;padding:0;background-color:#000000;color:#FFFFFF;font-family:helvetica,arial" onclick="location.href='$ad_url';return false;">
  <div id='highlight' style="position:relative;height:50px;background:-webkit-gradient(linear, left top, left bottom, from(rgba(255,255,255,0.35)),
    to(rgba(255,255,255,0.06))); -webkit-background-origin: padding-box; -webkit-background-clip: content-box;">
    <div style="position:absolute;right:0px;bottom:0px;color:#f00;margin:2px;font-size:smaller">
    Ads by InMobi
    </div>
    <div style="padding:15px 0 0 10px">
      $link_text
    </div>
  </div>
</body>
</html>""")
