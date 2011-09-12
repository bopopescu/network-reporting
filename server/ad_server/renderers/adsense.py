from ad_server.renderers.base_html_renderer import BaseHtmlRenderer          
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from common.utils import simplejson as json
        
class AdSenseRenderer(BaseHtmlRenderer):
    """ For now, just do the standard """
    
    TEMPLATE = "adsense.html"
    
    def _get_ad_type(self):
        # Override the adtype so that it requires a native adapter 
        # in-app and shows up as html in mobile web
        return 'adsense'
        
    def _setup_html_context(self):
        super(AdSenseRenderer, self)._setup_html_context()
        self.html_context['format'] = '320x50mb'
        self.html_context['title'] = ','.join(self.keywords)
        self.html_context['pub_id'] = self.adunit.get_pub_id('adsense_pub_id')
        self.html_context['channel_id'] = self.adunit.adsense_channel_id
        
    
    def _setup_headers(self):
        super(AdSenseRenderer, self)._setup_headers()
        params = {
          "Gclientid":str(self.adunit.get_pub_id("adsense_pub_id")),
          "Gcompanyname":str(self.adunit.account.adsense_company_name),
          "Gappname":str(self.adunit.app_key.adsense_app_name),
          "Gappid":str(self.adunit.app_key.adsense_app_name or '0'),
          "Gkeywords":str(self.keywords or ''),
          "Gtestadrequest":"0",
          "Gchannelids":str('[%s]'%self.adunit.adsense_channel_id or ''),        
        # "Gappwebcontenturl":,
          "Gadtype":"GADAdSenseTextImageAdType", 
          #GADAdSenseTextAdType,GADAdSenseImageAdType,GADAdSenseTextImageAdType
        # "Ghostid":,
        # "Gbackgroundcolor":"00FF00",
        # "Gadtopbackgroundcolor":"FF0000",
        # "Gadbordercolor":"0000FF",
        # "Gadlinkcolor":,
        # "Gadtextcolor":,
        # "Gadurlolor":,
        # "Gexpandirection":,
        # "Galternateadcolor":,
        # "Galternateadurl":, 
        # This could be interesting we can know if Adsense 'fails' and 
        # is about to show a PSA.
        # "Gallowadsafemedium":,
        }
        self.header_context.add_header("X-Nativeparams", json.dumps(params))
        self.header_context.add_header("X-Failurl", self.fail_url)
        self.header_context.add_header("X-Format",'300x250_as')
        self.header_context.add_header("X-Backgroundcolor","0000FF") 
        
