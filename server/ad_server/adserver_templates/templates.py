from string import Template

#
# Templates
#
TEMPLATES = {
    "adsense": Template("""<html>
                            <head>
                              <title>$title</title>
                              $finishLoad
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
                          </html> """),
    "iAd": Template("iAd"),
    "clear": Template(""),
    "text": Template("""<html>
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 14px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
                          $finishLoad
                          <script>
                            function webviewDidClose(){} 
                            function webviewDidAppear(){} 
                          </script>
                          <title>$title</title>
                        </head>
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">
                          <div class="creative"><div style="padding: 5px 10px;"><a href="$url" class="creative_headline">$headline</a><br/>$line1 $line2<br/><span class="creative_url"><a href="$url">$display_url</a></span></div></div>\
                          $trackingPixel
                        </body> </html> """),
    "text_icon": Template(
"""<html>
  <head>
    $finishLoad
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
</html>"""),
    "image":Template("""<html>
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 20px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
                          $finishLoad
                          <script>
                            function webviewDidClose(){} 
                            function webviewDidAppear(){} 
                          </script>
                        </head>
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">\
                          <a href="$url" target="_blank"><img src="$image_url" width=$w height=$h/></a>
                          $trackingPixel
                        </body></html> """),
    "admob": Template("""<html><head>
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
                         bgcolor: '000000', // background color (hex)
                         text: 'FFFFFF', // font-color (hex)
                         ama: false, // set to true and retain comma for the AdMob Adaptive Ad Unit, a special ad type designed for PC sites accessed from the iPhone.  More info: http://developer.admob.com/wiki/IPhone#Web_Integration
                         test: false, // test mode, set to false to receive live ads
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
                            var MAX_POLL = 2000;
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
                        </body></html>"""),
    "html":Template("""<html><head><title>$title</title>
                        $finishLoad
                        <script type="text/javascript">
                          function webviewDidClose(){}
                          function webviewDidAppear(){}
                          window.addEventListener("load", function() {
                            var links = document.getElementsByTagName('a');
                            for(var i=0; i < links.length; i++) {
                              links[i].setAttribute('target','_blank');
                            }
                          }, false);
                        </script></head>
                        <body style="margin:0;padding:0;">${html_data}$trackingPixel</body></html>"""),
    "html_full":Template("$html_data")
  }

