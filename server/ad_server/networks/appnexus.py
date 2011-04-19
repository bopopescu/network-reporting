from ad_server.networks.server_side import ServerSide

class AppNexusServerSide(ServerSide):
    base_url = "http://ib.sand-08.adnxs.net/sspt"
    def __init__(self,request,adunit=None,*args,**kwargs):
        return super(AppNexusServerSide,self).__init__(request,adunit,*args,**kwargs)
            
    def get_key_values(self):
        return {'calltype':'admeld',
                        'response_type':'iframe',
                        'member_code':'mopub',
                        'agent':3,
                        'inv_code':'testssp',
                        'user_id':self.get_udid(),
                        'referrer':'',
                        'ip_address':self.get_ip(),
                        'position':'above',
                        'size':'300x250',
                        'user_agent':self.get_user_agent()}
        
    def get_query_string(self):
        import urllib
        query_string = urllib.urlencode(self.get_key_values())             
        return query_string
    
    @property
    def url(self):
        return self.base_url + '?' + self.get_query_string()

    @property
    def headers(self):
        return {}        

    @property    
    def payload(self):
        return None

    def get_response(self):
        import urllib2
        req = urllib2.Request(self.url)
        response = urllib2.urlopen(req)    
        return response.read()
        
    def bid_and_html_for_response(self,response):
        from django.utils import simplejson
        import logging
        response_dict = simplejson.loads(response.content)        
        logging.warning(response_dict)
        return response_dict['bid']['cpm'],response_dict['bid']['creative'].replace("[admeld_win_price]",".09")