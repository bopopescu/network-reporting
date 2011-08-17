from string import Template
    
image = Template("""<html>
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
