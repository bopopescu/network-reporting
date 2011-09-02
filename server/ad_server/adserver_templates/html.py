from string import Template

html = Template("""<html>
                      $viewportMetaTag
                      <head><title>$title</title>
                        $finishLoad
                        $trackImpressionHelper
                        <script type="text/javascript">
                          function webviewDidClose(){
                            if(typeof webviewDidCloseHelper == 'function') {
                               webviewDidCloseHelper();
                            }
                          }
                          function webviewDidAppear(){
                              // inserts impression tracking
                              // when the interstitial is presented on screen
                              if(typeof trackImpressionHelper == 'function') {
                                trackImpressionHelper();
                              }
                          
                              // calls a user defined function if it exists
                              // useful for starting animations, videos, etc
                              // this would exist as part of the html for the 
                              // "html" creative
                              if(typeof webviewDidAppearHelper == 'function') { 
                                webviewDidAppearHelper(); 
                              }
                          }
                          window.addEventListener("load", function() {
                            var links = document.getElementsByTagName('a');
                            for(var i=0; i < links.length; i++) {
                              links[i].setAttribute('target','_top');
                            }
                          }, false);
                        </script>$network_style</head>
                        <body class="network_center" style="margin:0;padding:0;">
                                ${html_data}
                                $trackingPixel
                                <script type="text/javascript">
                                    if (typeof htmlWillCallFinishLoad == "undefined" || !htmlWillCallFinishLoad) { // just call mopubFinishLoad upon window's load
                                        if(typeof mopubFinishLoad == 'function') {
                                           window.onload = mopubFinishLoad;
                                        }
                                    }
                                </script>
                        </body></html>""")