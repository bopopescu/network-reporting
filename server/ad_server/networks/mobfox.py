from ad_server.networks.server_side import ServerSide

import cgi
import logging
import urllib
import urllib2

from xml.dom import minidom
from ad_server.debug_console import trace_logging

class MobFoxServerSide(ServerSide):
    base_url = "http://my.mobfox.com/request.php?v=api_mopub" # live
    pub_id_attr = 'mobfox_pub_id'
    network_name = 'MobFox'
    

    def __init__(self,request,adunit=None,*args,**kwargs):
        self.html_params = {}
        return super(MobFoxServerSide,self).__init__(request,adunit,*args,**kwargs)

    @property
    def url(self):
        return self.base_url

    @property  
    def payload(self):
        data = {'rt': 'api',
                'u': self.get_user_agent(),
                'i': self.get_ip(),
                'o': self.get_udid(),
                'm': 'live',
                's': self.get_pub_id(),
                # 'longitude': , # long
                # 'latitude': , # lat
                # 'int_cat': , # MobFox category type
                'v': 'api_mopub',
              }
              
        return urllib.urlencode(data) + '&' + self._add_extra_headers()
        
    def _add_extra_headers(self):
        """
        add extra headers to the post because shouldn't escape the brackets (e.g. h[])
        hence we can't just use the generic paylod method.
        return valid looks something like h[foo]=bar&h[foo2]=bar2
        """
        exclude_headers = ['Keep-Alive','Connection','Cookie','Cache-Control','Content-Length']
        headers = [] # list of (header,value) tuples
        # select only ones not in the exclue header list
        for header,value in self.request.headers.iteritems():
            if not header in exclude_headers:
                headers.append((header,value))
        return '&'.join(['h[%s]=%s'%(urllib.quote_plus(h),urllib.quote_plus(v)) for h,v in  headers])

    def get_response(self):
        req = urllib2.Request(self.url)
        response = urllib2.urlopen(req)
        return response.read()

    def _getText(self,node):
        return node.firstChild.data

    def parse_xml(self,document):
        try:
            dom = minidom.parseString(document)
        except:
            return None       
        
        request_elems = dom.getElementsByTagName("request")        
        # bail early if improper response
        if not request_elems:
            return None
            
        ad_type = request_elems[0].getAttribute("type")
        self.html_params.update(ad_type=ad_type)
        
        # helper so we don't repeat ourselves
        def _param_updater(param):
            elems = dom.getElementsByTagName(param)
            if elems:
                value = self._getText(elems[0])
                self.html_params.update({param:value})
            

        if ad_type == "imageAd":
            image_params = ["bannerwidth","bannerheight","clicktype","clickurl",
                            "imageurl","urltype","refresh","scale","skippreflight"]
            for param in image_params:
                _param_updater(param)
        elif ad_type == "textAd":
            text_params = ["htmlString","clicktype","clickurl","urltype","refresh"
                          "scale","skippreflight"]
            for param in text_params:
                _param_updater(param)
        elif ad_type == "noAd":
            ad_type = None            
        else:
            raise Exception("unsupported ad type")
        return ad_type    
         

    def _bid_and_html_for_response(self,response):
        image_template = """<div style='text-align:center'><a href="%(clickurl)s" target="_blank"><img src="%(imageurl)s" width=%(bannerwidth)s height=%(bannerheight)s/></a></div>"""
        text_template = """%(htmlString)s"""
        # Image: 
        # response.content = """<request type="imageAd"><bannerwidth>300</bannerwidth><bannerheight>50</bannerheight><clicktype>inapp</clicktype><clickurl>http://my.mobfox.com/activation-info.php</clickurl><imageurl>http://my.mobfox.com/documents/testbanner/300x50.jpg</imageurl><urltype>link</urltype><refresh>30</refresh><scale>no</scale><skippreflight>yes</skippreflight></request>"""
        # Text:
        # response.content = """<request type="textAd"><htmlString>&lt;style&gt;.afma{left:0;border:0px solid #ffffff;height:50px;overflow:hidden;position:relative;width:320px;background-color:#FFFFFF;background: url(http://my.mobfox.com/images/textad_bg.png); z-index:1;}.afma_target{display: block;height:20px;left:0;position:absolute;top:14px;width:320px;z-index:4;}.ad{display:table;border:none;height:50px;left:0;position:absolute;table-layout:fixed;top:0;width:299px;z-index:2}.ad_text{color:#000000;display:table-cell;font-family:helvetica,sans-serif;font-weight:bold;font-size:12px;height:100%;line-height:18px;overflow:hidden;text-align:center;text-overflow:ellipsis;white-space:nowrap;width:100%;vertical-align:middle}.icon{height:50px;left:301px;position:absolute;top:0;width:px;z-index:3}.gradient{border:none;height:50px;left:0;position:absolute;top:0;width:320px;z-index:1}.tag{color:#000000;font-size:14px;line-height:20px}.url{color:#006699;font-size:12px;line-height:14px}&lt;/style&gt;&lt;body leftmargin=&quot;0&quot; topmargin=&quot;0&quot; bgcolor=&quot;#ffffff&quot; marginheight=&quot;0&quot; marginwidth=&quot;0&quot;&gt;&lt;div class=&quot;afma&quot;&gt;&lt;a target=&quot;_top&quot; href=&quot;http://my.mobfox.com/clickthrough.do?ai=156&amp;ii=2f07e9a2ee8d929f9c083c0c789f89f1&quot; class=&quot;afma_target&quot; id=&quot;aw0&quot; onClick=&quot;if(animator){animator.stop();animator.reset()} ha('aw0')&quot;&gt;&lt;/a&gt;&lt;div id=&quot;gradient&quot; class=&quot;gradient&quot; style=&quot;&quot;&gt;&lt;/div&gt;&lt;div style=&quot;top: 0px;&quot; class=&quot;ad&quot; id=&quot;text1&quot;&gt;&lt;div class=&quot;ad_text&quot;&gt;&lt;span class=&quot;tag&quot;&gt;Text Ad Test Test Test Mopub&lt;/span&gt;&lt;br&gt;&lt;span class=&quot;url&quot;&gt;&lt;/span&gt;&lt;/div&gt;&lt;/div&gt;&lt;div class=&quot;ad&quot; id=&quot;text2&quot; style=&quot;visibility: visible; top: -48px;&quot;&gt;&lt;div class=&quot;ad_text&quot;&gt;&lt;br&gt;&lt;/div&gt;&lt;/div&gt;&lt;img class=&quot;icon&quot; src=&quot;http://my.mobfox.com/images/textad_sideimg.png&quot; width=&quot;19&quot; height=&quot;50&quot;&gt;&lt;/div&gt;</htmlString><clicktype>inapp</clicktype><clickurl>http://my.mobfox.com/clickthrough.do?ai=156&amp;ii=2f07e9a2ee8d929f9c083c0c789f89f1</clickurl><refresh>90</refresh><scale>no</scale><skippreflight>yes</skippreflight></request>"""
        # No Ad: 
        # response.content = """<requesttype="noAd"></request>"""
        trace_logging.warning("Received MobFox response: %s"%cgi.escape(response.content))
        ad_type = self.parse_xml(response.content)
        if ad_type == "imageAd":
            content = image_template % self.html_params
        elif ad_type == "textAd":    
            content = text_template % self.html_params
        else:    
            trace_logging.info("MobFox ad is empty")
            raise Exception("MobFox ad is empty")
        return 0.0, content
        
        