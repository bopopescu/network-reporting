from string import Template

from ad_server.renderers.creative_renderer import BaseCreativeRenderer 
from google.appengine.api.images import InvalidBlobKeyError
from google.appengine.api import images

class ImageRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, headers, 
                                        creative=None,  
                                        format_tuple=None,
                                        context=None,
                                        keywords=None,
                                        adunit=None,
                                        **kwargs):                 
        img_height = creative.image_height
        img_width = creative.image_width

        try:        
            context["image_url"] = images.get_serving_url(creative.image_blob) 
        except InvalidBlobKeyError:     
            # This will fail when on mopub-experimental
            trace_logging.warning("""InvalidBlobKeyError when trying to get image from adhandler.py.
                                    Are you on mopub-experimental?""")

        # if full screen we don't need to center
        if (not "full" in adunit.format) or ((img_width == 480.0 and img_height == 320.0 ) or (img_width == 320.0 and img_height == 480.0)):
            css_class = ""
        else:
            css_class = "center"    

        context.update({"w": img_width, "h": img_height, "w2":img_width/2.0, "h2":img_height/2.0, "class":css_class})
                                        
     
    TEMPLATE = Template("""<html>
                          <meta name="viewport" content="width=device-width; initial-scale=1.0; user-scalable=no;">
                            <head>                          
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
                              <style type='text/css'>
                                .center {
                                    position: fixed;
                                    top: 50%;
                                    left: 50%;
                                    margin-left: -${w2}px !important;
                                    margin-top: -${h2}px !important;
                                    }
                              </style>
                            </head>
                            <body style="padding:0;margin:0;">
                              <div class="outer" id="outer">    
                                  <div class="${class}">    
                                      <a href="$url" target="_top"><img src="$image_url" width="$w" height="$h"/></a>
                                  </div>
                              </div>      
                              $trackingPixel
                            </body></html> """)
                                                