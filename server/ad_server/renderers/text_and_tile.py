from string import Template    
from ad_server.renderers.text import TextRenderer
from google.appengine.api.images import InvalidBlobKeyError
from google.appengine.api import images 

class TextAndTileRenderer(TextRenderer):
    """ For now, just do the standard """
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

        try:
            context["image_url"] = images.get_serving_url(creative.image_blob)   
        except InvalidBlobKeyError:     
            # This will fail when on mopub-experimental
            trace_logging.warning("""InvalidBlobKeyError when trying to get image from adhandler.py.
                                  Are you on mopub-experimental?""")     
        if creative.action_icon:
            #c.url can be undefined, don't want it to break
            icon_div = '<div style="padding-top:5px;position:absolute;top:0;right:0;"><a href="'+(creative.url or '#')+'" target="_top">'
            if creative.action_icon:
                icon_div += '<img src="http://' + request_host + '/images/' + creative.action_icon+'.png" width=40 height=40/></a></div>'
            context["action_icon_div"] = icon_div 
        else:
            context['action_icon_div'] = ''                      
        context['action_icon']=creative.action_icon
        context['color']=creative.color
        context['font_color']=creative.font_color
        context['gradient']=creative.gradient
        context['w'] = creative.width or ''
        context['h'] = creative.height or ''
        context['url'] = creative.url or ''
        context['display_url'] = creative.display_url or ''
        
        super(TextAndTileRenderer, cls).network_specific_rendering(header_context, 
                                                                   creative=creative,  
                                                                   format_tuple=format_tuple,
                                                                   context=context,
                                                                   keywords=keywords,
                                                                   adunit=adunit,
                                                                   **kwargs)

            
###### TEMPLATE #########
           
    TEMPLATE = Template(
    """<html>
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
        <title></title>
      </head>
      <body style="top-margin:0;margin:0;width:320px;padding:0;background-color:#$color;font-size:12px;font-family:Arial,sans-serif;">
      <div id='highlight' style="position:relative;height:50px;background:-webkit-gradient(linear, left top, left bottom, from(rgba(255,255,255,0.35)),
        to(rgba(255,255,255,0.06))); -webkit-background-origin: padding-box; -webkit-background-clip: content-box;">
        <div style="margin:5px;width:40px;height:40px;float:left"><img id="thumb" src="$image_url" style="-webkit-border-radius:6px;-moz-border-radius:6px" width=40 height=40/></div>
        <div style="float:left;width:230">
          <div style="color:white;font-weight:bold;margin:0px 0 0 5px;padding-top:8;">$line1</div>
          <div style="color:white;margin-top:6px;margin:5px 0 0 5px;">$line2</div>
        </div>
        $action_icon_div
        $trackingPixel
      </div>
      </body>
    </html>""")
                                             
