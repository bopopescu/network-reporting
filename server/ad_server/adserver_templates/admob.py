from string import Template

admob = Template("""<html><head>
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
                        </body></html>""")
