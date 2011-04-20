import hashlib
import re


class ServerSide(object):
    base_url = "http://www.test.com/ad?"
    def __init__(self,request,adunit=None,*args,**kwargs):
        self.request = request
        self.adunit = adunit
   
    @property
    def format(self):
        return self.adunit.format
    
    def get_udid(self,udid=None):
        """
        udid from the device comes as 
        udid=md5:asdflkjbaljsadflkjsdf (new clients) or
        udid=pqesdlsdfoqeld (old clients)
        
        For the newer clients we can just pass over the hashed string
        after "md5:"
        
        For older clients we must md5 hash the udid with salt 
        "mopub-" prepended.
        
        returns hashed_udid
        
        """  
        raw_udid = udid or self.request.get('udid')
        raw_udid_parts = raw_udid.split('md5:')
        
        # if has md5: then just pull out value
        if len(raw_udid_parts) == 2:
            # get the part after 'md5:'
            hashed_udid = raw_udid_parts[-1]
        # else salt the udid and hash it    
        else:
            m = hashlib.md5()
            m.update('mopub-')
            m.update(raw_udid_parts[0])
            hashed_udid = m.hexdigest().upper()
        return hashed_udid    
       
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
   
    def _get_size(self,content):
            width_pat = re.compile(r'width="(?P<width>\d+?)"')
            height_pat = re.compile(r'height="(?P<height>\d+?)"')
   
            width_match = re.search(width_pat,content)
            height_match = re.search(height_pat,content)
   
            width = 0
            height = 0
            if height_match and width_match:
                width = int(width_match.groups('width')[0])
                height = int(height_match.groups('height')[0])
            return width,height            
   
    def bid_and_html_for_response(self,response):
        return 0.0,"<html>BLAH</html>"    
       