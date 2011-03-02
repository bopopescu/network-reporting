from ad_server.networks.server_side import ServerSide
import urllib
import urllib2
import string

class JumptapServerSide(ServerSide):
  base_url = "http://a.jumptap.com/a/ads" # live

  def get_key_values(self):
    return {'pub': self.get_account().jumptap_pub_id,
            #'gateway-ip': '208.54.5.50',  # TODO: This should be the x-forwarded-for header of the device
            'hid': self.get_udid(),
            #'site': 'pa_mopub_inc_simpleadsdemo_drd_app',  # TODO: Site ID from Jumptap, ugh
            #'spot': 'pa_mopub_inc_simpleadsdemo_drd_app_adspot',  # TODO: Spot ID from Jumptap, double ugh
            'client-ip': self.get_ip(), # Test value: 'client-ip': '208.54.5.50'
            'v': 'v29' }

  def get_query_string(self):
    query_string = urllib.urlencode(self.get_key_values())       
    return query_string

  @property
  def url(self):
    return self.base_url + '?' + self.get_query_string()

  @property
  def headers(self):
    return { 'User-Agent': self.get_user_agent() }
             #'Accept-Language': 'en-us' }  # TODO: Accept language from web request

  def get_response(self):
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)
    return response.read()

  def bid_and_html_for_response(self,response):
    if len(response.content) == 0:
      raise Exception("Jumptap ad is empty")

    return 0.0,"<html><body style='margin:0;padding:0;'><div style='text-align:center'>"+response.content+"</div></body></html>"