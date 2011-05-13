from string import Template

image = Template("""<html>
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 20px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
                          $finishLoad
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
                        <body class= style="margin:0;padding:0;">
                          <div class="center">    
                              <a href="$url" target="_top"><img src="$image_url" width="$w" height="$h"/></a>
                          </div>
                          $trackingPixel
                        </body></html> """)
