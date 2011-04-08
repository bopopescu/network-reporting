from ad_server.networks.server_side import ServerSide
import re, urllib, urllib2, string
import logging

from xml.dom import minidom

class InMobiServerSide(ServerSide):
  base_url = "http://w.inmobi.com/showad.asm" # live
  def __init__(self,request,adunit,*args,**kwargs):
    self.url_params = {}
    return super(InMobiServerSide,self).__init__(request,adunit,*args,**kwargs)

  @property
  def url(self):
    return self.base_url

  def get_inmobi_user_agent(self):
    ua = self.get_user_agent();
    if "Android" in ua:
      return 'InMobi_AndroidSDK=1.1 (Specs)'
    if "iPad" in ua:
      return ua  

    # TODO: Should return actual software and hardware versions for iPhone/iPod
    return 'InMobi_Specs_iPhoneApp=1.0.2 (iPhone; iPhone OS 3.1.2; HW iPhone1,1)'

  def get_inmobi_ad_size(self):
    if self.adunit.format == "300x250" or self.adunit.format == 'full' or self.adunit.format == 'full_landscape':
      self.url_params.update(width=300,height=250)
      return '10'
    if self.adunit.format == "728x90":
      self.url_params.update(width=728,height=90)
      return '11'
    if self.adunit.format == "160x600":
      # InMobi returns 120x600 non-IAB format
      self.url_params.update(width=120,height=600)
      return '13'

    # By default, InMobi supports a 320x48 banner
    self.url_params.update(width=320,height=48)
    return '9'

  @property
  def headers(self):
    return {'X-Mkhoj-SiteID': self.get_account().inmobi_pub_id,
            'X-InMobi-Phone-UserAgent': self.get_user_agent() }

  @property  
  def payload(self):
    data = {'mk-siteid': self.get_account().inmobi_pub_id,
            'mk-version': 'pr-SPEC-ATATA-2009052',
            # 'u-id': self.get_udid(),
            # 'mk-carrier': self.get_ip(),
            # 'mk-carrier': '117.97.87.6',  # Test value
            'mk-ad-slot': self.get_inmobi_ad_size(),
            'h-user-agent': self.get_inmobi_user_agent(),
            'format': 'xml' }
            
            
            
    return "mk-carrier=117.97.87.6 \
            &mk-siteid=4028cb962ca1c524012ccdb55c3801bf \
            &mk-version=pr-SPEC-ATATA-2009052 \
            &h-user-agent=Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10 \
            &format=xml"        
    #return urllib.urlencode(data)

  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)
    return response.read()

  def _getText(self,node):
      return node.childNodes[0].data

  def parse_xml(self,document):
    try:
      dom = minidom.parseString(document)
    except:
      return

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
    # Simple Banner
    #response.content = '<AdResponse><Ads number="1"><Ad type="banner" actionType="android"><ImageURL>http://r.w.inmobi.com/FileData/513cc422-33a6-4274-9e22-dd12e84e23d14.png</ImageURL><ImageAltText></ImageAltText><Placement>page</Placement><AdURL>http://c.w.mkhoj.com/c.asm/3/t/c7i/pl5/2/2m/aj/u/0/0/1/354957037659003/11ba085a-012e-1000-d9a8-00020fe80003/1/829a0c01</AdURL></Ad></Ads></AdResponse>'
    # Simple Text/image (also banner)
    #response.content = '<AdResponse><Ads number="1"><Ad type="text" actionType="web"><LinkText>Sick of being overweight? Get Free Guide</LinkText><Placement>page</Placement><AdURL>http://c.w.mkhoj.com/c.asm/3/t/c7i/pl5/2/2m/aj/u/0/0/1/354957037659003/1217ae48-012e-1000-de75-00020ff10003/1/9c3e6541</AdURL></Ad></Ads></AdResponse>'
    # Simple MRect/Image
    #reponse.content = '
    logging.warning('response: %s'%response.content)
    if re.match("^<!--.*--\>$", response.content) == None and len(response.content) != 0:
      # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
      self.parse_xml(response.content)
      if 'image_url' in self.url_params:
        return 0.0, banner_template.safe_substitute(self.url_params)
      elif 'link_text' in self.url_params:
        return 0.0, text_template.safe_substitute(self.url_params)

    raise Exception("InMobi ad is empty")

banner_template = string.Template(
"""
  <div style='text-align:center'><a href="$ad_url" target="_blank"><img src="$image_url"/></a></div>
""")

text_template = string.Template(
"""
  <style type="text/css">
   body { background-color:#000000; color:#FFFFFF; font-family:helvetica,arial }
  </style>  
  <div id='highlight' style="position:relative;height:${height}px;background:-webkit-gradient(linear, left top, left bottom, from(rgba(255,255,255,0.35)),to(rgba(255,255,255,0.06)));
    -webkit-background-origin: padding-box; -webkit-background-clip: content-box;" onclick="window.open('$ad_url');return false;">
    <div style="padding:15px 0 0 10px">
      $link_text
    </div>
    <div style="position:absolute;right:0px;bottom:0px;color:#f00;margin:2px;font-size:70%">
    Ads by InMobi
    </div>
  </div>
""")
