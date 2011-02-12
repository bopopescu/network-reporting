from ad_server.networks.server_side import ServerSide
import logging
import re
import urllib2
import string
import time

from xml.dom import minidom

class BrightRollServerSide(ServerSide):
  base_url = "http://mobile.btrll.com/adwhirl/req/?adFeedKey=506"
  base_url = "http://vast.bp3844869.btrll.com/vast/"
  def __init__(self,request,adunit,*args,**kwargs):
    self.url_params = {}
    self.pub_id = adunit.account.brightroll_pub_id
    return super(BrightRollServerSide,self).__init__(request,adunit,*args,**kwargs)
  
  @property
  def url(self):
    pub_id = self.pub_id or 3844792 
    return self.base_url + str(pub_id) or + '?n=%f'%time.time()
    
  @property
  def headers(self):
    # TODO: Replace with self.get_appid()
    return {}

  @property  
  def payload(self):
    return None
    
  def get_response(self):
    logging.info("url: %s"%self.url)
    req = urllib2.Request(self.url)
    response = urllib2.urlopen(req)  
    return response.read()

  def _getText(self,node):
      return node.childNodes[0].data     
    
  def _getURL(self,node):
      return self._getText(node)    
    
  def parse_xml(self,document):
    logging.info(document)
    dom = minidom.parseString(document)
    ad = dom.getElementsByTagName("Ad")[0]
    inline = dom.getElementsByTagName("InLine")[0]
    
    # get impression_url
    impressions = inline.getElementsByTagName("Impression")
    logging.warning("impressions: %s"%impressions)
    
    impression_url = self._getURL(impressions[0])
    # TODO: get rid of multiple impression_url's in the template
    start_url = ''#self._getURL()
    # start_url = self._getURL(impressions[1])
        
    self.url_params.update(impression_url=impression_url,start_url=start_url)
                        
    tracking_events = inline.getElementsByTagName("TrackingEvents")[0].\
                        getElementsByTagName("Tracking")
    
    # get start_url, midpoint_url, complete_url
    for tracking_event in tracking_events:
        #names: start, midpoint, complete
        name = tracking_event.getAttribute("event")
        url = self._getURL(tracking_event)
        self.url_params.update({'%s_url'%name:url})
        
    video = inline.getElementsByTagName("Creative")[0]
    
    # get video_clickthrough_url
    video_clickthrough_url = self._getURL(video.getElementsByTagName("VideoClicks")[0].\
                             getElementsByTagName("ClickThrough")[0])
    self.url_params.update(video_clickthrough_url=video_clickthrough_url)
    
    # get video_height, video_width, video_url
    video_media = video.getElementsByTagName("MediaFiles")[0].\
                  getElementsByTagName("MediaFile")[0]
    video_width = video_media.getAttribute("width")
    video_height = video_media.getAttribute("height")
    video_url = self._getURL(video_media)
    self.url_params.update(video_width=video_width,video_height=video_height,
                           video_url=video_url)
    
    companion_image = self._getURL(inline.getElementsByTagName("CompanionAds")[0].\
                                   getElementsByTagName("StaticResource")[0])
    self.url_params.update(companion_image=companion_image)                               
    
    # get cpm
    cpm = self._getText(inline.getElementsByTagName("Extensions")[0].\
            getElementsByTagName("Extension")[0].\
            getElementsByTagName("Price")[0])
    self.url_params.update(cpm=cpm)
    
  def bid_and_html_for_response(self,response):
    self.parse_xml(response.content)
    # try:
    #     self.parse_xml(response.content)
    # except:
    #     raise Exception("BrightRoll ad is empty") 
    scripts = """
    <script type="text/javascript">
        window.addEventListener("load", function() { window.location="mopub://finishLoad";}, false);
        function webviewDidAppear(){playAdVideo();};
        //function webviewDidAppear(){alert(window.innerWidth+" "+window.innerHeight)};
        windowInnerWidth = 320;
    </script>"""     
           
    self.url_params.update(mopub_scripts=scripts) 
    logging.info(self.url_params)   
    return self.url_params.get('cpm'),template.safe_substitute(self.url_params)
    # return 0.0,string.replace(response.content,"<head>","<head><script type=\"text/javascript\">\nwindow.addEventListener(\"load\", function() { loadAdVideo();playAdVideo();}, false);function webviewDidAppear(){playAdVideo();}\n</script>",1)
    #return 0.0, "<html><body>hi</body></html>"
    #return 0.0,response.content
    
    
template = string.Template("""
    <!DOCTYPE HTML> 
    <html> 
    	<head id="head"> 
    	   <!-- BEGIN MoPub injection --> 
    	   $mopub_scripts
           <!-- END MoPub injection --> 
     	
    	
    		<script type="text/javascript"> 
    			var success = "success"; //tells iphone that there is an ad.  The iPhone can't grab the status code for a UIWebView

          var urls = {
            companionImage: "$companion_image",
            imp: [ "$impression_url", "$start_url" ],
            mid: [ "$midpoint_url" ],
            end: [ "$complete_url" ],
            landing: "$video_clickthrough_url"
          }

          function goToLanding(delay)
          {
            document.body.removeChild(document.getElementById("center"));
            document.getElementById("loader").style.display = "";
            delay = delay || 0;
            setTimeout(function(){ document.location.href = urls.landing }, delay);
          }

          function fireEvents(eventUrls, callback)
          {
            eventUrls.forEach(function(url)
            {
              var pixel = document.createElement('img');
              pixel.width = 0;
              pixel.height = 0;
              pixel.src = url;
              pixel.onload = callback;
              document.body.appendChild(pixel);
            });
    			}

    			function isIOS3()
    			{
    				var key = "iPhone OS ";
    				var index = navigator.userAgent.indexOf(key);
    				if (index > -1)
    				{
    					return navigator.userAgent.charAt(index + key.length) == "3";
    				}
    				else
    				{
    					return false;
    				}
    			}

    			function justPlayAdVideo()
    			{
    				adVideo.load();
    				adVideo.play();

            fireEvents(urls.imp);
    			}

    			function playAdVideo()
    			{
    				if(isIOS3())
    				{
    					var link = document.createElement("a");
    					link.addEventListener("click", function(e)
    					{
    						e.preventDefault();
    						justPlayAdVideo();
    					});
    					document.body.appendChild(link);
    					var clickEvent = document.createEvent("MouseEvents");
    					clickEvent.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
    					link.dispatchEvent(clickEvent);
    					document.body.removeChild(link);
    				}
    				else
    				{
    					justPlayAdVideo();
    				}
    			}

    			function loadAdVideo()
    			{
    				adVideo = document.getElementById("adVideo");
    				var firedMid = false;

            adVideo.addEventListener('loadeddata', function()
            {
              document.getElementById("loader").style.display = "none";
            });

    				adVideo.addEventListener('timeupdate', function()
    				{
    					if(!firedMid && ((2 * adVideo.currentTime) >= adVideo.duration))
    					{
                fireEvents(urls.mid);
    						firedMid = true;
    					}
    				});

    				adVideo.addEventListener('ended', function()
    				{
              fireEvents(urls.end, goToLanding);

              if (isIOS3())
              {
                goToLanding(500);
              }
    				});

    				adVideo.addEventListener('pause', function()
    				{
              goToLanding(500);
    				});
    			}

          function layoutElements()
          {
            var meta = document.createElement("meta");
            meta.name = "viewport";
            meta.content = "width=device-width,minimum-scale=1.0,maximum-scale=1.0";

            document.getElementById("head").appendChild(meta);
            document.getElementById("loader").style.display = "";
          }
    		</script> 
    	</head> 

    	<body style="background-color: black; width: 320px; height: 480px" onload="loadAdVideo()"> 
        <img id="loader" src="http://amscdn.btrll.com/production/3411/ajax-loader.gif" style="position:fixed;top:50%;left:50%;margin-top:-8px;margin-left:-8px;display:none"/>
    		<center id="center"> 
    			<!-- Dynamically Generate the Following Line --> 
    			<video src="$video_url" width="$video_width" height="$video_height" id="adVideo" controls="true"></video> 
    		</center> 
    		<script></script><!-- If you remove this line, the video won't autoplay in iOS3 :-\  --> 
    	</body> 
    </html>
    """)    