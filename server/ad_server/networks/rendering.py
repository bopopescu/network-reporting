from ad_server.adserver_templates import TEMPLATES
from ad_server.debug_console import trace_logging   
import random  
import re

class CreativeRenderer(object):
    
    @classmethod
    def render(cls, response, 
                    creative=None, 
                    adunit=None, 
                    keywords=None,
                    request_host=None,
                    request_url=None,   
                    version_number=None,
                    track_url=None,
                    on_fail_exclude_adgroups=None,
                    random_val=random.random()):
        # rename network so its sensical
        if creative.adgroup.network_type:
            creative.name = creative.adgroup.network_type

        trace_logging.info("##############################")
        trace_logging.info("##############################")
        trace_logging.info("Winner found, rendering: %s" % creative.name.encode('utf8') if creative.name else 'None')
        trace_logging.warning("Creative key: %s" % str(creative.key()))
        trace_logging.warning("rendering: %s" % creative.ad_type)

        template_name = creative.ad_type    
        
        format = adunit.format.split('x')
        network_center = False
        if len(format) < 2:
            ####################################
            # HACK FOR TUNEWIKI
            # TODO: We should make this smarter
            # if the adtype is not html (e.g. image)
            # then we set the orientation to only landscape
            # and the format to 480x320
            ####################################
            if not creative.ad_type == "html":
                if adunit.landscape:
                    response.headers.add_header("X-Orientation","l")
                    format = ("480","320")
                else:
                    response.headers.add_header("X-Orientation","p")
                    format = (320,480)    
                                            
            elif not creative.adgroup.network_type or creative.adgroup.network_type in FULL_NETWORKS:
                format = (320,480)
            elif creative.adgroup.network_type:
                #TODO this should be a littttleee bit smarter. This is basically saying default
                #to 300x250 if the adunit is a full (of some kind) and the creative is from
                #an ad network that doesn't serve fulls
                network_center = True
                if adunit.landscape:
                    response.headers.add_header("X-Orientation","l")
                else:
                    response.headers.add_header("X-Orientation","p")
                format = (300, 250)
        params = {}
        
        params.update(creative.__dict__.get("_entity"))
        #Line1/2 None check biznass 
        if params.has_key('line1'):
            if params['line1'] is None:
                params['line1'] = ''
        if params.has_key('line2'):
            if params['line2'] is None:
                params['line2'] = ''
        #centering non-full ads in fullspace
        if network_center: 
            #css to center things
            style = "<style type='text/css'> \
                          .network_center { \
                              position: fixed; \
                              top: 50%%; \
                              left: 50%%; \
                              margin-left: -%dpx !important; \
                              margin-top: -%dpx !important; \
                              } \
                      </style>"  
            params.update({'network_style': style % tuple(a/2 for a in format)})
        else:
            params.update({'network_style':''})
        #success tracking pixel for admob
        #set up an invisible span
        hidden_span = 'var hid_span = document.createElement("span"); hid_span.setAttribute("style", "display:none");'
        #init an image, give it the right src url, pixel size, append to span
        tracking_pix = 'var img%(name)s = document.createElement("img"); \
                        img%(name)s.setAttribute("height", 1); \
                        img%(name)s.setAttribute("width", 1);\
                        img%(name)s.setAttribute("src", "%(src)s");\
                        hid_span.appendChild(img%(name)s);'
      
        # because we send the client the HTML, and THEN send requests to admob for content, just becaues our HTML 
        # (in this case the tracking pixel) works, DOESNT mean that admob has successfully returned a creative.
        # Because of the admob pixel has to be added AFTER the admob ad actually loads, this is done via javascript.

        success = hidden_span
        success += tracking_pix % dict(name = 'first', src = track_url)           
        
        
        
        # We need randomness in order to keep clients from caching impression pixels
        if creative.tracking_url:
            creative.tracking_url += '&random=%s' % random_val
            success += tracking_pix % dict(name = 'second', src = creative.tracking_url) 
            params.update(trackingPixel='<span style="display:none;"><img src="%s"/><img src="%s"/></span>'% (creative.tracking_url, track_url))
        else:
            params.update(trackingPixel='<span style="display:none;"><img src="%s"/></span>' % track_url)
        success += 'document.body.appendChild(hid_span);'
        
        
        
        if creative.ad_type == "adsense":
            params.update({"title": ','.join(keywords), "adsense_format": '320x50_mb', "w": format[0], "h": format[1], "client": adunit.get_pub_id("adsense_pub_id")})
            params.update(channel_id=adunit.adsense_channel_id or '')
        elif creative.ad_type == "admob":
            params.update({"title": ','.join(keywords), "w": format[0], "h": format[1], "client": adunit.get_pub_id("admob_pub_id")})   
            
            # params.update(test_mode='true' if debug else 'false')
            # params.update(test_ad='<a href="http://m.google.com" target="_top"><img src="/images/admob_test.png"/></a>' if debug else '')
            response.headers.add_header("X-Launchpage","http://c.admob.com/")
        elif creative.ad_type == "text_icon":      
            try:
                params["image_url"] = images.get_serving_url(creative.image_blob)   
            except InvalidBlobKeyError:     
                # This will fail when on mopub-experimental
                trace_logging.warning("""InvalidBlobKeyError when trying to get image from adhandler.py.
                                      Are you on mopub-experimental?""")     
            if creative.action_icon:
                #c.url can be undefined, don't want it to break
                icon_div = '<div style="padding-top:5px;position:absolute;top:0;right:0;"><a href="'+(creative.url or '#')+'" target="_top">'
                if creative.action_icon:
                    icon_div += '<img src="http://' + request_host + '/images/' + creative.action_icon+'.png" width=40 height=40/></a></div>'
                params["action_icon_div"] = icon_div 
            else:
                params['action_icon_div'] = ''
            # response.headers.add_header("X-Adtype", str('html'))
        elif creative.ad_type == "greystripe":
            params.update({"html_data": creative.html_data, "w": format[0], "h": format[1]})
            response.headers.add_header("X-Launchpage","http://adsx.greystripe.com/openx/www/delivery/ck.php")
            template_name = "html"

        elif creative.ad_type == "image":                       
            img_height = creative.image_height
            img_width = creative.image_width

            try:        
                params["image_url"] = images.get_serving_url(creative.image_blob) 
            except InvalidBlobKeyError:     
                # This will fail when on mopub-experimental
                trace_logging.warning("""InvalidBlobKeyError when trying to get image from adhandler.py.
                                        Are you on mopub-experimental?""")
            
        
            # if full screen we don't need to center
            if (not "full" in adunit.format) or ((img_width == 480.0 and img_height == 320.0 ) or (img_width == 320.0 and img_height == 480.0)):
                css_class = ""
            else:
                css_class = "center"    
        
            params.update({"w": img_width, "h": img_height, "w2":img_width/2.0, "h2":img_height/2.0, "class":css_class})
        elif creative.ad_type == "html":
            params.update({"html_data": creative.html_data, "w": format[0], "h": format[1]})
        
            if 'full' in adunit.format:
                params['trackingPixel'] = ""
                trackImpressionHelper = "<script>\nfunction trackImpressionHelper(){\n%s\n}\n</script>"%success
                params.update(trackImpressionHelper=trackImpressionHelper)
            else:
                params['trackImpressionHelper'] = ''    
        
            # add the launchpage header for inmobi in case they have dynamic ads that use
            # window.location = 'http://some.thing/asdf'
            if creative.adgroup.network_type == "inmobi":
                response.headers.add_header("X-Launchpage","http://c.w.mkhoj.com")

        
        elif creative.ad_type == "html_full":
            # must pass in parameters to fully render template
            # TODO: NOT SURE WHY I CAN'T USE: html_data = c.html_data % dict(track_pixels=success)
            html_data = creative.html_data.replace(r'%(track_pixels)s',success)
            params.update(html_data=html_data)
            response.headers.add_header("X-Scrollable","1")
            response.headers.add_header("X-Interceptlinks","0")
        elif creative.ad_type == "text":  
            response.headers.add_header("X-Productid","pixel_001")
      
      
        if version_number >= 2:  
            params.update(finishLoad='<script>function mopubFinishLoad(){window.location="mopub://finishLoad";}</script>')
            # extra parameters used only by admob template
            #add in the success tracking pixel
            params.update(admob_finish_load= success + 'window.location = "mopub://finishLoad";')
            params.update(admob_fail_load='window.location = "mopub://failLoad";')
        else:
            # don't use special url hooks because older clients don't understand    
            params.update(finishLoad='')
            # extra parameters used only by admob template
            params.update(admob_finish_load=success)
            params.update(admob_fail_load='')
    
        # indicate to the client the winning creative type, in case it is natively implemented (iad, clear)
    
        if str(creative.ad_type) == "iAd":
            # response.headers.add_header("X-Adtype","custom")
            # response.headers.add_header("X-Backfill","alert")
            # response.headers.add_header("X-Nativeparams",'{"title":"MoPub Alert View","cancelButtonTitle":"No Thanks","message":"We\'ve noticed you\'ve enjoyed playing Angry Birds.","otherButtonTitle":"Rank","clickURL":"mopub://inapp?id=pixel_001"}')
            # response.headers.add_header("X-Customselector","customEventTest")
            if "full_tablet" in adunit.format:
                response.headers.add_header("X-Adtype", "interstitial")
                response.headers.add_header("X-Fulladtype", "iAd_full")
            else:
                response.headers.add_header("X-Adtype", str(creative.ad_type))
                response.headers.add_header("X-Backfill", str(creative.ad_type))
        
            response.headers.add_header("X-Failurl", _build_fail_url(request_url, on_fail_exclude_adgroups))

        elif str(creative.ad_type) == "admob_native":
            if "full" in adunit.format:
                response.headers.add_header("X-Adtype", "interstitial")
                response.headers.add_header("X-Fulladtype", "admob_full")
            else:
                response.headers.add_header("X-Adtype", str(creative.ad_type))
                response.headers.add_header("X-Backfill", str(creative.ad_type))
            response.headers.add_header("X-Failurl", _build_fail_url(request_url, on_fail_exclude_adgroups))
            nativeparams_dict = {
                "adUnitID":adunit.get_pub_id("admob_pub_id"),
                "adWidth":adunit.get_width(),
                "adHeight":adunit.get_height()
            }
            response.headers.add_header("X-Nativeparams", simplejson.dumps(nativeparams_dict))

        elif str(creative.ad_type) == "millennial_native":
            if "full" in adunit.format:
                response.headers.add_header("X-Adtype", "interstitial")
                response.headers.add_header("X-Fulladtype", "millennial_full")
            else:
                response.headers.add_header("X-Adtype", str(creative.ad_type))
                response.headers.add_header("X-Backfill", str(creative.ad_type))
            response.headers.add_header("X-Failurl", _build_fail_url(request_url, on_fail_exclude_adgroups))
            nativeparams_dict = {
                "adUnitID":adunit.get_pub_id("millennial_pub_id"),
                "adWidth":adunit.get_width(),
                "adHeight":adunit.get_height()
            }
            response.headers.add_header("X-Nativeparams", simplejson.dumps(nativeparams_dict))
        
        elif str(creative.ad_type) == "adsense":
            response.headers.add_header("X-Adtype", str(creative.ad_type))
            response.headers.add_header("X-Backfill", str(creative.ad_type))
        
            trace_logging.warning('pub id:%s' % adunit.get_pub_id("adsense_pub_id"))
            header_dict = {
              "Gclientid":str(adunit.get_pub_id("adsense_pub_id")),
              "Gcompanyname":str(adunit.account.adsense_company_name),
              "Gappname":str(adunit.app_key.adsense_app_name),
              "Gappid":str(adunit.app_key.adsense_app_name or '0'),
              "Gkeywords":str(keywords or ''),
              "Gtestadrequest":"0",
              "Gchannelids":str('[%s]'%adunit.adsense_channel_id or ''),        
            # "Gappwebcontenturl":,
              "Gadtype":"GADAdSenseTextImageAdType", #GADAdSenseTextAdType,GADAdSenseImageAdType,GADAdSenseTextImageAdType
              "Gtestadrequest":"0",
            # "Ghostid":,
            # "Gbackgroundcolor":"00FF00",
            # "Gadtopbackgroundcolor":"FF0000",
            # "Gadbordercolor":"0000FF",
            # "Gadlinkcolor":,
            # "Gadtextcolor":,
            # "Gadurlolor":,
            # "Gexpandirection":,
            # "Galternateadcolor":,
            # "Galternateadurl":, # This could be interesting we can know if Adsense 'fails' and is about to show a PSA.
            # "Gallowadsafemedium":,
            }
            json_string_pairs = []
            for key,value in header_dict.iteritems():
                json_string_pairs.append('"%s":"%s"'%(key, value))
            json_string = '{'+','.join(json_string_pairs)+'}'
            response.headers.add_header("X-Nativeparams", json_string)
        
            # add some extra  
            response.headers.add_header("X-Failurl", _build_fail_url(request_url, on_fail_exclude_adgroups))
            response.headers.add_header("X-Format",'300x250_as')
       
            response.headers.add_header("X-Backgroundcolor","0000FF")
        elif creative.ad_type == "custom_native":
            creative.html_data = creative.html_data.rstrip(":")
            params.update({"method": creative.html_data})
            response.headers.add_header("X-Adtype", "custom")
            response.headers.add_header("X-Customselector",creative.html_data)

        elif str(creative.ad_type) == 'admob':
            response.headers.add_header("X-Failurl", _build_fail_url(request_url, on_fail_exclude_adgroups))
            response.headers.add_header("X-Adtype", str('html'))
        else:  
            response.headers.add_header("X-Adtype", str('html'))
      
    
        # pass the creative height and width if they are explicity set
        trace_logging.warning("creative size:%s"%creative.format)
        if creative.width and creative.height and 'full' not in adunit.format:
            response.headers.add_header("X-Width", str(creative.width))
            response.headers.add_header("X-Height", str(creative.height))
    
        # adds network info to the headers
        if creative.adgroup.network_type:
            response.headers.add_header("X-Networktype",creative.adgroup.network_type)

        if creative.launchpage:
            response.headers.add_header("X-Launchpage", creative.launchpage)
    
        # render the HTML body
        rendered_creative = TEMPLATES[template_name].safe_substitute(params)
        rendered_creative.encode('utf-8')
    
    
        return rendered_creative               
        
        

########### HELPER FUNCTIONS ############
def _build_fail_url(original_url, on_fail_exclude_adgroups):
    """ Remove all the old &exclude= substrings and replace them with our new ones """
    clean_url = re.sub("&exclude=[^&]*", "", original_url)

    if not on_fail_exclude_adgroups:
        return clean_url
    else:
        return clean_url + '&exclude=' + '&exclude='.join(on_fail_exclude_adgroups)

