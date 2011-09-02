from ad_server.networks.server_side import ServerSide
import urllib
import urllib2
from ad_server.debug_console import trace_logging
from ad_server.networks.server_side import ServerSideException  
class GreyStripeServerSide(ServerSide):    
    """ Greystripe is being deprecated. """
    base_url = "http://adsx.greystripe.com/openx/www/delivery/mw2.php"
    pub_id_attr = 'greystripe_pub_id'
    network_name = 'GreyStripe'
    
    
    @property
    def url(self):
        return self.base_url
      
    @property
    def headers(self):
      # TODO: Replace with self.get_appid()
        return {'User-Agent': self.client_context.user_agent}

    @property    
    def payload(self):
        data = {'language':'python',
                'version':'1.0',
                'format':'html',
                'ip': self.client_context.client_ip,
                'site_id': self.get_pub_id(),
                }
        return urllib.urlencode(data)
    
    def get_response(self):
        req = urllib2.Request(self.url)
        response = urllib2.urlopen(req)  
        return response.read()
      
    def html_for_response(self, response):
        if len(response.content) == 0 or \
        response.status_code != 200 or \
        """<script type='text/javascript'>/*<![CDATA[*/<a href='F' target='_blank'><img src='F' border='0' alt=''></a>/*]]>*/</script""" in response.content:
            trace_logging.info("GreyStripe failed to return ad")
            raise ServerSideException("GreyStripe ad is empty")  
        return response.content
