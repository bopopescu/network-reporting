from string import Template   
import random                 
from ad_server.renderers.creative_renderer import BaseCreativeRenderer

class AdMobRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, header_context, 
                                        creative=None,  
                                        format_tuple=None,
                                        context=None,
                                        keywords=None,
                                        adunit=None,
                                        **kwargs):   
        context.update({"title": ','.join(keywords), "w": format_tuple[0], "h": format_tuple[1], "client": adunit.get_pub_id("admob_pub_id"), \
        "bgcolor": str(adunit.app_key.admob_bgcolor or '000000') , "textcolor": str(adunit.app_key.admob_textcolor or 'FFFFFF')})  
        
        # context.update(test_mode='true' if debug else 'false')
        # context.update(test_ad='<a href="http://m.google.com" target="_top"><img src="/images/admob_test.png"/></a>' if debug else '')
        header_context.add_header("X-Launchpage","http://c.admob.com/")

###### TEMPLATE #########

    TEMPLATE = Template("""<html><head>
                        <script type="text/javascript">
                          function webviewDidClose(){} 
                          function webviewDidAppear(){} 
                          window.innerWidth = $w;
                          window.innerHeight = $h;
                        </script>
                        <title>$title</title>
                        </head><body style="margin: 0;width:${w}px;height:${h}px;padding:0;background-color:transparent;">
                        <script type="text/javascript">
                        var admob_vars = {
                         pubid: '$client', // publisher id
                         bgcolor: '$bgcolor', // background color (hex)
                         text: '$textcolor', // font-color (hex)
                         ama: false, // set to true and retain comma for the AdMob Adaptive Ad Unit, a special ad type designed for PC sites accessed from the iPhone.  More info: http://developer.admob.com/wiki/IPhone#Web_Integration
                         test: $test_mode, // test mode, set to false to receive live ads
                         manual_mode: true // set to manual mode
                        };
                        </script>
                        <script type="text/javascript" src="http://mmv.admob.com/static/iphone/iadmob.js"></script>  
                        
                        <!-- DIV For admob ad -->
                        <div id="admob_ad">
                        </div>

                        <!-- Script to determine if admob loaded -->
                        <script>
                            var ad = _admob.fetchAd(document.getElementById('admob_ad'));                                                                         
                            var POLLING_FREQ = 500;
                            var MAX_POLL = 5000;
                            var polling_timeout = 0;                                                                                                              
                            var polling_func = function() {                                                                                                       
                             if(ad.adEl.height == 48) {                                                                                                           
                               // we have an ad                                                                                                                   
                               console.log('received ad');
                               $admob_finish_load
                             } 
                             else if(polling_timeout < MAX_POLL) {                                                                                                         
                               console.log('repoll');                                                                                                             
                               polling_timeout += POLLING_FREQ;                                                                                                           
                               window.setTimeout(polling_func, POLLING_FREQ);                                                                                             
                             }                                                                                                                                    
                             else {                                                                                                                               
                               console.log('no ad'); 
                               $admob_fail_load                                                                                                               
                               ad.adEl.style.display = 'none';                                                                                                    
                             }                                                                                                                                    
                            };                                                                                                                                    
                            window.setTimeout(polling_func, POLLING_FREQ);
                        </script>
                        </body></html>""")

