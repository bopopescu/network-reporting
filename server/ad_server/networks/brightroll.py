from ad_server.networks.server_side import ServerSide
import logging
import re
import urllib2
import string
import time

from xml.dom import minidom
from ad_server.networks.server_side import ServerSideException  

class BrightRollServerSide(ServerSide):
    base_url = "http://vast.bp3844869.btrll.com/vast/"
    pub_id_attr = 'brightroll_pub_id'
    no_pub_id_warning = 'Warning: no %s Publisher ID has been specified using demo account'
    network_name = 'BrightRoll'
    
  
    def __init__(self,request,adunit,*args,**kwargs):
        self.url_params = {}
        return super(BrightRollServerSide,self).__init__(request,adunit,*args,**kwargs)
    
    @property
    def payload(self):
        return None

    @property
    def url(self):
        pub_id = self.get_pub_id() or 3844792 
        return self.base_url + str(pub_id) + '?n=%f'%time.time()
            
    @property
    def headers(self):
        # TODO: Replace with self.get_appid()
        return {}

    def get_response(self):
        logging.info("url: %s"%self.url)
        req = urllib2.Request(self.url)
        response = urllib2.urlopen(req)    
        return response.read()

    def _getText(self,node):
        return node.childNodes[0].data     
      
    def _getURL(self,node):
        return str(self._getText(node))
      
    def parse_xml(self, document):
        logging.info(document)
        
        dom = minidom.parseString(document)
        ad = dom.getElementsByTagName("Ad")[0]
        inline = dom.getElementsByTagName("InLine")[0]
        
        
        ############################
        # Get Tracking information #
        ############################
        impression_urls = []
        midpoint_urls = []
        end_urls = []
        click_urls = []
        
        impressions = inline.getElementsByTagName("Impression")
        for impression in impressions:
            impression_urls.append(self._getURL(impression))
            
                            
        tracking_events = inline.getElementsByTagName("TrackingEvents")[0].\
                            getElementsByTagName("Tracking")
        
        # get start_url, midpoint_url, complete_url
        for tracking_event in tracking_events:
            #names: start, midpoint, complete
            name = tracking_event.getAttribute("event")
            if name == "midpoint":
                midpoint_urls.append(self._getURL(tracking_event))
            elif name == "complete":
                end_urls.append(self._getURL(tracking_event))    
        
        
        video_clicks = inline.getElementsByTagName("VideoClicks")[0]
        
        click_urls.append(self._getURL(inline.getElementsByTagName("ClickThrough")[0]))
        # this is weird, but what brightroll wants
        # not always there
        click_tracking_urls = inline.getElementsByTagName("ClickTracking")
        if click_tracking_urls:
            end_urls.append(self._getURL(click_tracking_urls[0]))
        
        # update the params
        self.url_params.update(impression_urls=impression_urls,
                               midpoint_urls=midpoint_urls,
                               end_urls=end_urls,
                               click_urls=click_urls,
                               visit_us_url=click_urls[0])
        
        ##################################
        # Get video creative information #
        ##################################
        video = inline.getElementsByTagName("Creative")[0]
        
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
        
        ####################
        # Get Realtime CPM #
        ####################
        try:
            cpm = self._getText(inline.getElementsByTagName("Extensions")[0].\
                    getElementsByTagName("Extension")[0].\
                    getElementsByTagName("Price")[0])
        except:
            cpm = None            
        self.url_params.update(cpm=cpm)
        
    def html_for_response(self, response):
        if response == '<VAST version="2.0" />':
            raise ServerSideException
        
        try:
            self.parse_xml(response.content)
        except IndexError:
            raise ServerSideException("BrightRoll xml parsing failed...empty ad?")
        # scripts = """
        # <script type="text/javascript">
        #     window.addEventListener("load", function() { window.location="mopub://finishLoad";}, false);
        #     function webviewDidAppear(){playAdVideo(); %(track_pixels)s;};
        #     //function webviewDidAppear(){alert(window.innerWidth+" "+window.innerHeight)};
        #     windowInnerWidth = 320;
        # </script>"""  
        #        
        # self.url_params.update(mopub_scripts=scripts) 
        logging.info(self.url_params)   
        return template.safe_substitute(self.url_params)
        # return 0.0,string.replace(response.content,"<head>","<head><script type=\"text/javascript\">\nwindow.addEventListener(\"load\", function() { loadAdVideo();playAdVideo();}, false);function webviewDidAppear(){playAdVideo();}\n</script>",1)
        #return 0.0, "<html><body>hi</body></html>"
        #return 0.0,response.content
        
        
template = string.Template("""
<style type="text/css">
	        body {
	            background-color: black;
	            width: 320px;
	            height: 480px;
	        }
	    </style>
		<script type="text/javascript"> 
		    document.body.onload = loadAdVideo;
		    
		    function webviewDidAppearHelper(){
		        playAdVideo();
		    }
		
			var success = "success"; //tells iphone that there is an ad.  The iPhone can't grab the status code for a UIWebView

    var urls = {
      companionImage: "$companion_image",
      imp: $impression_urls,
      mid: $midpoint_urls,
      end: $end_urls,
      landing: $click_urls
    }

    function goToLanding(delay)
    {
      document.body.removeChild(document.getElementById("center"));
      document.getElementById("loader").style.display = "";
      delay = delay || 0;
      setTimeout(function(){ document.location.href = urls.landing[0] }, delay);
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
	
	
    <img id="loader" src="http://amscdn.btrll.com/production/3411/ajax-loader.gif" style="position:fixed;top:50%;left:50%;margin-top:-8px;margin-left:-8px;display:none"/>
		<center id="center"> 
			<!-- Dynamically Generate the Following Line --> 
			<video src="$video_url" width="$video_width" height="$video_height" id="adVideo" controls="true"></video> 
		</center> 
		<script></script><!-- If you remove this line, the video won't autoplay in iOS3 :-\  --> 
""")    
    
template2 = string.Template("""<!DOCTYPE HTML> 
<html> 
  <head> 
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=0" /> 
    $mopub_scripts
    <script type="text/javascript"> 
      var impUrls = $impression_urls;
      var midUrls = $midpoint_urls;
      var endUrls = $end_urls;
      var clickUrls = $click_urls;
 
      var videoUrl = "$video_url";
      var videoWidth = $video_width;
      var videoHeight = $video_height;
      var visitUsUrl = "$visit_us_url";
 
      var visitUsImageUrl = "http://amscdn.btrll.com/production/4604/BR_iPhone_ViewSite_Button_G57x57.png";
      var activityIndicatorUrl = "http://amscdn.btrll.com/production/3411/ajax-loader.gif";
 
      //Set these dynamically -- they are parsed by the webview.  Separate url values with spaces
      //<companion-url>http://brxserv.btrll.com/v1/epix/6834979/3844869/2668/5268/QbS2X4JgAAAABNmmBkAAAKbAAAFJQAOqsFAAATEQBLEz5iDZzoTA/event.imp/r_64.aHR0cDovL2JyeGNkbi5idHJsbC5jb20vcHJvZHVjdGlvbi8yODIzNi9pbnRlbF8zMjB4NTBfdjMuZ2lm</companion-url>
      //<ad-title>FullVideo_SoundOn</ad-title>
 
      var video;
      var showCloseTime = 7;
      var clearShowCloseTime = 0;
 
      function goToVisitUsUrl()
      {
        sendWebView("willGoToVisitUsUrl");
        video.pause();
        showActivityIndicator();
        fireEvents(clickUrls, 1000, function(){
          window.location.href = visitUsUrl;
        });
      }
 
      function fireEvents(eventUrls, timeout, callback)
      {
        //sendWebView("log", { message: "fireEvents:\\n" + eventUrls.join("\\n") });
        eventUrls.forEach(function(url)
        {
          var completed = 0;
 
          var pixel = document.createElement('img');
          pixel.width = 0;
          pixel.height = 0;
          pixel.src = url;
          pixel.onload = function()
          {
            completed ++;
            if ((completed == eventUrls.length) && callback)
            {
              clearTimeout(timeoutId);
              callback();
            }
          }
          document.body.appendChild(pixel);
        });
 
        var timeoutId = setTimeout(function(){
          if (callback)
          {
            callback();
            callback = null;
          }
        }, timeout);
      }
 
      var sendsToWebview = true;
      function disableDelegateMessages()
      {
        sendsToWebview = false;
      }
 
      disableDelegateMessages();
 
      function sendWebView(messageName, messageArgs)
      {
        if (sendsToWebview)
        {
          var i;
          var separator = "?";
          var query = "";
          if (messageArgs)
          {
            var name;
            for (name in messageArgs)
            {
              query = query + separator + name + "=" + messageArgs[name];
              separator = "&";
            }
          }
 
          window.location.href = "http://brightRollAd/" + messageName + query;
        }
      }
 
      function videoPlayed()
      {
        sendWebView("videoStarted");
        hideActivityIndicator();
        fireEvents(impUrls);
      }
 
      var firedMid = false;
      var firstFrame = true;
      function videoAdvanced()
      {
        if (firstFrame)
        {
          firstFrame = false;
          videoPlayed();
        }
        else
        {
          firstFrame = false;
        }
 
        if (showCloseTimeout && (video.currentTime > clearShowCloseTime))
        {
          clearTimeout(showCloseTimeout);
          showCloseTimeout = null;
        }
 
        if(video.duration)
        {
          var t = String(Math.floor(video.duration - video.currentTime));
          if (t.length == 1)
          {
            t = "0" + t;
          }
          document.getElementById("countdown").innerHTML = ":" + t;
        }
 
        if(!firedMid && ((2*video.currentTime) >= video.duration))
        {
          fireEvents(midUrls);
          firedMid = true;
        }
      }
 
      var wasPaused = false;
      function videoPaused()
      {
        wasPaused = true;
        video.removeEventListener(videoPaused);
        if(isIOS3())
        {
          goToVisitUsUrl();
        }
      }
 
      function resumeVideo()
      {
        if (wasPaused)
        {
          wasPaused = false;
          video.addEventListener("pause", videoPaused);
          video.play();
        }
      }
 
      function videoPlayedThrough()
      {
        fireEvents(endUrls, 1000, endUrlsFired);
      }
 
      function endUrlsFired()
      {
        sendWebView("videoPlayedThrough");
        if(isIOS3())
        {
          goToVisitUsUrl();
        }
      }
 
      function setupVideo()
      {
        video = document.getElementById("video");
        //video.addEventListener("play", videoPlayed);
        video.addEventListener("timeupdate", videoAdvanced);
        video.addEventListener("pause", videoPaused);
        video.addEventListener("ended", videoPlayedThrough);
        video.src = videoUrl;
        showCloseTimeout = setTimeout(function(){ sendWebView("videoLoadingSlowly") }, showCloseTime * 1000);
      }
 
      function setupActivityIndicator()
      {
        document.getElementById("activityIndicator").src = activityIndicatorUrl;
      }
 
      function showActivityIndicator()
      {
        document.getElementById("statusRow").style.display = "none";
        document.getElementById("videoRow").style.display = "none";
        document.getElementById("controlsRow").style.display = "none";
        document.getElementById("activityIndicatorRow").style.display = "table-row";
      }
 
      function hideActivityIndicator()
      {
        document.getElementById("videoRow").style.display = "table-row";
        document.getElementById("activityIndicatorRow").style.display = "none";
      }
 
      function setupVisitUs()
      {
        document.getElementById("visitUsImage").src = visitUsImageUrl;
        document.getElementById("visitUsLink").addEventListener("click", function(e)
        {
          e.preventDefault();
          goToVisitUsUrl();
        });
      }
 
      var initialStatusDivHeight;
      function applyLayout()
      {
        var padding = 8;
        document.body.style.height = window.innerHeight + "px";
 
        var statusDiv = document.getElementById("statusDiv");
        var statusDivHeight = statusDiv.offsetHeight + padding;
        if (!initialStatusDivHeight && statusDivHeight)
        {
          initialStatusDivHeight = statusDivHeight;
        }
        if (statusDivHeight != initialStatusDivHeight)
        {
          statusDivHeight = initialStatusDivHeight;
        }
        statusDiv.style.height = statusDivHeight + "px";
 
        var controlsDivHeight = document.getElementById("controlsDiv").offsetHeight + padding;
        var videoRatio = videoWidth/videoHeight;
 
        var availableWidth = window.innerWidth;
        var availableHeight = window.innerHeight - statusDivHeight - controlsDivHeight;
 
        document.getElementById("activityIndicatorCell").style.height = availableHeight + "px";
 
        if(videoRatio > availableWidth/availableHeight)
        {
          var newWidth = Math.min(availableWidth, videoWidth);
          var newHeight = newWidth/videoRatio;
        }
        else
        {
          var newHeight = Math.min(availableHeight, videoHeight);
          var newWidth = videoRatio*newHeight;
        }
 
        video.style.width = newWidth + "px";
        video.style.height = newHeight + "px";
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
 
      var playInterval;
      function playVideo()
      {
        if(isIOS3())
        {
          hideActivityIndicator();
          setTimeout(playiOS3Video, 500);
        }
        else
        {
          justPlayVideo();
        }
      }
 
      function justPlayVideo()
      {
        alert("here");
        video.load();
        video.play();
      }
 
      function playiOS3Video()
      {
        var link = document.createElement("a");
        link.addEventListener("click", function(e)
        {
          e.preventDefault();
          justPlayVideo();
        });
        document.body.appendChild(link);
        var clickEvent = document.createEvent("MouseEvents");
        clickEvent.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
        link.dispatchEvent(clickEvent);
        document.body.removeChild(link);
      }
 
      window.addEventListener("load", function(){
        document.addEventListener("touchmove", function(e){ e.preventDefault(); });
 
        setupVideo();
        setupActivityIndicator();
        setupVisitUs();
        playVideo();
        setInterval(applyLayout, 200);
        
        // MOPUB NATIVE CLIENT HOOK
        window.location="mopub://finishLoad";
      });
 
    </script> 
    <style type="text/css"> 
      *
      {
        margin: 0px;
        padding: 0px;
        background-color: black;
        color: white;
        font-family: 'Arial Rounded MT Bold';
        font-size: 11px;
      }
 
      html
      {
        height: 100%;
      }
 
      body
      {
        height: 100%;
      }
 
      td
      {
        vertical-align: middle;
      }
 
      #statusRow td
      {
        vertical-align: top;
      }
 
      #statusDiv
      {
        padding: 4px;
      }
 
      #videoRow
      {
        display: none;
      }
 
      #videoRow td
      {
        width: 100%;
        height: 100%;
        background-color: black;
      }
 
      #controlsDiv
      {
        padding: 4px;
      }
    </style> 
  </head> 
 
  <body>
    <table cellpadding="0" cellspacing="0" width="100%" height="100%"> 
      <tr id="statusRow"> 
        <td align="center"> 
          <div id="statusDiv">Ads by BrightRoll <span id="countdown"></span></div> 
        </td> 
      </tr> 
      <tr id="activityIndicatorRow"> 
        <td id="activityIndicatorCell" align="center"> 
          <img id="activityIndicator" /> 
        </td> 
      </tr> 
      <tr id="videoRow"> 
        <td align="center"> 
          <video id="video" webkit-playsinline></video> 
        </td> 
      </tr> 
      <tr id="controlsRow"> 
        <td align="center"> 
          <div id="controlsDiv"><a id="visitUsLink" href="#"><img id="visitUsImage" /></a></div> 
        </td> 
      </tr> 
    </table> 
    <script></script> 
  </body> 
</html>
""")    



### EXAMPLE VAST RESPONSE
sample_response = """<?xml version="1.0" encoding="UTF-8"?> 
<VAST version="2.0"> 
  <Ad id="brightroll_ad"> 
    <InLine> 
      <AdSystem>BrightRoll</AdSystem> 
      <AdTitle></AdTitle> 
      <Impression><![CDATA[http://2686.btrll.com/imp/2686/5573/PreRoll.182.112431/start;Video;1301955275]]></Impression> 
      <Impression><![CDATA[http://brxserv.btrll.com/v1/epix/6834979/3844792/2668/4881/DbzBx_CgKbAABNmkLLAAAKbAAAExEAOqq4AAAAAABc5buF6_RLfQ/event.imp/r_64.aHR0cDovL2Iuc2NvcmVjYXJkcmVzZWFyY2guY29tL3A_YzE9MSZjMj02MDAwMDA2JmMzPSZjND0mYzU9MDEwMDAwJmM2PTY4MzQ5NzkmYzEwPSZjQTE9OCZjQTI9NjAwMDAwNiZjQTM9Mzg0NDc5MiZjQTQ9MjY2OCZjQTU9ODkzJmNBNj02ODM0OTc5JmNBMTA9NDg4MSZjdj0xLjcmY2o9JnJuPTEzMDE5NTUyNzUmcj1odHRwJTNBJTJGJTJGcGl4ZWwucXVhbnRzZXJ2ZS5jb20lMkZwaXhlbCUyRnAtY2I2QzB6RkY3ZFdqSS5naWYlM0ZsYWJlbHMlM0RwLjY4MzQ5NzkuMzg0NDc5Mi4wJTJDYS44OTMuMjY2OC40ODgxJTJDdS5wcmUuMHgwJTNCbWVkaWElM0RhZCUzQnIlM0QxMzAxOTU1Mjc1]]></Impression> 
      <Impression><![CDATA[http://2686.btrll.com/imp/2686/5573/PreRoll.182.112432/start;Video;1301955275]]></Impression> 
      <Creatives> 
        <Creative sequence="1"> 
          <Linear> 
            <Duration>00:00:15</Duration> 
            <TrackingEvents> 
              <Tracking event="midpoint"><![CDATA[http://brxserv.btrll.com/v1/epix/6834979/3844792/2668/4881/DbzBx_CgKbAABNmkLLAAAKbAAAExEAOqq4AAAAAABc5buF6_RLfQ/event.mid/r_64.aHR0cDovLzI2ODYuYnRybGwuY29tL2ltcC8yNjg2LzU1NzMvUHJlUm9sbC4xODIuMTEyNDMxL21pZDtWaWRlbzsxMzAxOTU1Mjc1]]></Tracking> 
              <Tracking event="midpoint"><![CDATA[http://2686.btrll.com/imp/2686/5573/PreRoll.182.112432/mid;Video;1301955275]]></Tracking> 
              <Tracking event="complete"><![CDATA[http://brxserv.btrll.com/v1/epix/6834979/3844792/2668/4881/DbzBx_CgKbAABNmkLLAAAKbAAAExEAOqq4AAAAAABc5buF6_RLfQ/event.end/r_64.aHR0cDovLzI2ODYuYnRybGwuY29tL2ltcC8yNjg2LzU1NzMvUHJlUm9sbC4xODIuMTEyNDMxL2RvbmU7VmlkZW87MTMwMTk1NTI3NQ]]></Tracking> 
              <Tracking event="complete"><![CDATA[http://2686.btrll.com/imp/2686/5573/PreRoll.182.112432/done;Video;1301955275]]></Tracking> 
            </TrackingEvents> 
            <VideoClicks> 
              <ClickThrough><![CDATA[http://brxserv.btrll.com/v1/epix/6834979/3844792/2668/4881/DbzBx_CgKbAABNmkLLAAAKbAAAExEAOqq4AAAAAABc5buF6_RLfQ/event.click/r_64.aHR0cDovL3d3dy5pbnRlbC5jb20]]></ClickThrough> 
              <ClickTracking><![CDATA[http://brxserv.btrll.com/v1/epix/6834979/3844792/2668/4881/DbzBx_CgKbAABNmkLLAAAKbAAAExEAOqq4AAAAAABc5buF6_RLfQ/event.c_trk/r_64.aHR0cDovLzI2ODYuYnRybGwuY29tL2Nsay8yNjg2LzU1NzMvUHJlUm9sbC4xODIuMTEyNDMxL25vbmUvO1ZpZGVvOzEzMDE5NTUyNzU]]></ClickTracking> 
            </VideoClicks> 
            <MediaFiles> 
              <MediaFile delivery="progressive" type="video/x-flv" bitrate="400" height="240" width="320"><![CDATA[http://brxcdn2.btrll.com/production/26753/FullVideo_SoundOn.mp4]]></MediaFile> 
            </MediaFiles> 
          </Linear> 
        </Creative> 
        <Creative sequence="1"> 
          <CompanionAds> 
            <Companion width="320" height="50"> 
              <StaticResource creativeType="image/jpeg"><![CDATA[http://brxserv.btrll.com/v1/epix/6834979/3844792/2668/5268/IbzBx_CgAAAABNmkLLAAAKbAAAFJQAOqq4AAATEQAvf9LlkcUTsA/event.imp/r_64.aHR0cDovL2JyeGNkbi5idHJsbC5jb20vcHJvZHVjdGlvbi8yODIzNi9pbnRlbF8zMjB4NTBfdjMuZ2lm]]></StaticResource> 
              <CompanionClickThrough><![CDATA[http://brxserv.btrll.com/v1/epix/6834979/3844792/2668/5268/IbzBx_CgAAAABNmkLLAAAKbAAAFJQAOqq4AAATEQAvf9LlkcUTsA/event.click/r_64.aHR0cDovL3d3dy5pbnRlbC5jb20]]></CompanionClickThrough> 
            </Companion> 
          </CompanionAds> 
        </Creative> 
      </Creatives> 
      <Extensions> 
        <Extension type="LR-Pricing"> 
          <Price model="CPM" currency="USD">5</Price> 
        </Extension> 
      </Extensions> 
    </InLine> 
  </Ad> 
</VAST>
"""                                                                      
