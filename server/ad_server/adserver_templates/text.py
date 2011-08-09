from string import Template

text = Template("""<html>
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 14px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
                          $finishLoad
                          <script>
                            if(typeof finishLoad == 'function') {
                                finishLoad();
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
