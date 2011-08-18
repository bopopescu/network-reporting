from string import Template

from string import Template   
import random                 
from ad_server.renderers.creative_renderer import BaseCreativeRenderer

class AdsenseRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, headers, 
                                        creative=None, 
                                        adunit=None,  
                                        format_tuple=None,
                                        context=None,
                                        **kwargs):   
        context.update({"title": ','.join(keywords), "adsense_format": '320x50_mb', "w": format_tuple[0], "h": format_tuple[1], "client": adunit.get_pub_id("adsense_pub_id")})
        context.update(channel_id=adunit.adsense_channel_id or '')     
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
