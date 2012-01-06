from ad_server.renderers.base_html_renderer import BaseHtmlRenderer          
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from common.utils import simplejson as json
        
class AdSenseRenderer(BaseHtmlRenderer):
    """
    Uses custom adsense TEMPLATE for rendering
    
    Inheritance Hierarchy:  
    AdSenseRenderer => BaseHtmlRenderer => BaseCreativeRenderer
    """
    
    TEMPLATE = "adsense.html"
    
    def _get_ad_type(self):
        """
        Override the adtype so that it requires a native adapter 
        in-app and shows up as html in mobile web
         """
        return 'adsense'
        
    def _setup_html_context(self):
        super(AdSenseRenderer, self)._setup_html_context()
        if self.adunit.get_width() == 300 and self.adunit.get_height() == 250:
            self.html_context['format'] = '300x250_mb'
        else:
            self.html_context['format'] = '320x50_mb'
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
        self.header_context.native_params = json.dumps(params)
        self.header_context.fail_url = self.fail_url
        self.header_context.format = '300x250_as'
        self.header_context.background_color = "0000FF"
        
