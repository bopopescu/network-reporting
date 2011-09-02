from string import Template   
import random                 
from ad_server.renderers.base_html_renderer import BaseHtmlRenderer

class TextRenderer(BaseHtmlRenderer):
    @classmethod
    def network_specific_rendering(cls, header_context, 
                                   creative=None,  
                                   format_tuple=None,
                                   context=None,
                                   keywords=None,
                                   adunit=None,
                                   fail_url=None,
                                   request_host=None,
                                   **kwargs):   
        
        context['line1']=creative.line1 or ''
        context['line2']=creative.line2 or ''
        context['w'] = creative.width or ''
        context['h'] = creative.height or ''
        context['url'] = creative.url or ''
        context['display_url'] = creative.display_url or ''
        try:
            context['headline']=creative.headline or ''
        except AttributeError:
            pass
        
        super(TextRenderer, cls).network_specific_rendering(header_context, 
                                                            creative=creative,  
                                                            format_tuple=format_tuple,
                                                            context=context,
                                                            keywords=keywords,
                                                            adunit=adunit,
                                                            **kwargs)

        

    TEMPLATE = Template("""<html>
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 14px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
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
                          <title>$title</title>
                        </head>
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">
                          <div class="creative"><div style="padding: 5px 10px;"><a href="$url" class="creative_headline">$headline</a><br/>$line1 $line2<br/><span class="creative_url"><a href="$url">$display_url</a></span></div></div>\
                          $trackingPixel
                        </body> </html> """)
