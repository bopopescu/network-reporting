from string import Template

from string import Template   
import random                 
from ad_server.renderers.creative_renderer import BaseCreativeRenderer          

from ad_server.debug_console import trace_logging

class AdSenseRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, header_context, 
                                        creative=None, 
                                        adunit=None,  
                                        format_tuple=None,
                                        context=None,     
                                        keywords=None,
                                        fail_url=None,
                                        **kwargs):   
        context.update({"title": ','.join(keywords), "adsense_format": '320x50_mb', "w": format_tuple[0], "h": format_tuple[1], "client": adunit.get_pub_id("adsense_pub_id")})
        context.update(channel_id=adunit.adsense_channel_id or '')  
        
        
        header_context.add_header("X-Adtype", str(creative.ad_type))
        header_context.add_header("X-Backfill", str(creative.ad_type))
        
        trace_logging.warning('pub id:%s' % adunit.get_pub_id("adsense_pub_id"))
        header_dict = {
          "Gclientid":str(adunit.get_pub_id("adsense_pub_id")),
          "Gcompanyname":str(adunit.account.adsense_company_name),
          "Gappname":str(adunit.app_key.adsense_app_name),
          "Gappid":str(adunit.app_key.adsense_app_name or '0'),
          "Gkeywords":str(keywords or ''),
          "Gtestadrequest":"0",
          "Gchannelids":str('[%s]'%adunit.adsense_channel_id or ''),        
        # "Gappwebcontenturl":,
          "Gadtype":"GADAdSenseTextImageAdType", #GADAdSenseTextAdType,GADAdSenseImageAdType,GADAdSenseTextImageAdType
          "Gtestadrequest":"0",
        # "Ghostid":,
        # "Gbackgroundcolor":"00FF00",
        # "Gadtopbackgroundcolor":"FF0000",
        # "Gadbordercolor":"0000FF",
        # "Gadlinkcolor":,
        # "Gadtextcolor":,
        # "Gadurlolor":,
        # "Gexpandirection":,
        # "Galternateadcolor":,
        # "Galternateadurl":, # This could be interesting we can know if Adsense 'fails' and is about to show a PSA.
        # "Gallowadsafemedium":,
        }
        json_string_pairs = []
        for key,value in header_dict.iteritems():
            json_string_pairs.append('"%s":"%s"'%(key, value))
        json_string = '{'+','.join(json_string_pairs)+'}'
        header_context.add_header("X-Nativecontext", json_string)
        
        # add some extra  
        header_context.add_header("X-Failurl", fail_url)
        header_context.add_header("X-Format",'300x250_as')
        
        header_context.add_header("X-Backgroundcolor","0000FF") 
        header_context.add_header("X-Adtype", str('html'))    
        
###### TEMPLATE #########

    TEMPLATE = Template("""<html>
                            <head>
                              <title>$title</title>
                              $finishLoad
                              <script> 
                                if(typeof mopubFinishLoad == 'function') {
                                    window.onload = mopubFinishLoad;
                                }
                              </script>
                              <script>
                                function webviewDidClose(){} 
                                function webviewDidAppear(){} 
                              </script>
                            </head>
                            <body style="margin: 0;width:${w}px;height:${h}px;" >
                              <script type="text/javascript">window.googleAfmcRequest = {client: '$client',ad_type: 'text_image', output: 'html', channel: '$channel_id',format: '$adsense_format',oe: 'utf8',color_border: '336699',color_bg: 'FFFFFF',color_link: '0000FF',color_text: '000000',color_url: '008000',};</script> 
                              <script type="text/javascript" src="http://pagead2.googlesyndication.com/pagead/show_afmc_ads.js"></script>  
                              $trackingPixel
                            </body>
                          </html> """)
