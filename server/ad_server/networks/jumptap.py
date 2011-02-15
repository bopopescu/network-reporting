from ad_server.networks.server_side import ServerSide
import urllib
import urllib2
import string

class JumptapServerSide(ServerSide):
  base_url = "http://a.jumptap.com/a/ads" # live
  def __init__(self,request,adunit,*args,**kwargs):
    self.url_params = {}
    return super(JumptapServerSide,self).__init__(request,adunit,*args,**kwargs)

  @property
  def url(self):
    return self.base_url

  @property
  def headers(self):
    return { 'User-Agent': self.get_user_agent(),
             'Accept-Language': 'en-us' }  # TODO: Accept language from web request

  @property  
  def payload(self):
    # TODO: Replace with self.get_appid()
    data = {'pub': self.get_account().jumptap_pub_id,
            'gateway-ip': '',  # TODO: This should be the x-forwarded-for header of the device
            'hid': self.get_udid(),
            'site': 'pa_mopub_inc_simpleadsdemo_drd_app'  # TODO: Site ID from Jumptap, ugh
            'spot': 'pa_mopub_inc_simpleadsdemo_drd_app_adspot'  # TODO: Spot ID from Jumptap, double ugh
            'client-ip': self.get_ip(), # Test value: 'mk-carrier': '208.54.5.50'
            'v': 'v29' }

    return urllib.urlencode(data)

  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)
    return response.read()

  def bid_and_html_for_response(self,response):
    if len(response.content) == 0:
      raise Exception("Jumptap ad is empty")

    return "<html><body>"+response.content+"</body></html>"

banner_template = string.Template(
"""<!DOCTYPE HTML>
<html>
<body style="margin:0;width:320px;height:48px;padding:0;" onclick="location.href='$ad_url';return false;">
  <img src="$image_url" width=320 height=48/>
</body>
</html>""")

text_template = string.Template(
"""<!DOCTYPE HTML>
<html>
<body style="margin:0;width:320px;height:48px;padding:0;background-color:#000000;color:#FFFFFF;font-family:helvetica,arial" onclick="location.href='$ad_url';return false;">
  <div id='highlight' style="position:relative;height:50px;background:-webkit-gradient(linear, left top, left bottom, from(rgba(255,255,255,0.35)),
    to(rgba(255,255,255,0.06))); -webkit-background-origin: padding-box; -webkit-background-clip: content-box;">
    <div style="padding:15px 0 0 10px">
      $link_text
    </div>
    <div style="position:absolute;right:0px;bottom:0px;color:#f00;margin:2px;font-size:70%">
    Ads by InMobi
    </div>
  </div>
</body>
</html>""")
