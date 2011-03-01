/*
	MoPub Client JS
*/
(function(){
    if (window.mopub_ad_unit == null) {
        console.log("MoPub load failed. mopub_ad_unit needs to be defined.");
        return;
    }

    if (window.mopub_ad_width == null)
        window.mopub_ad_width = 320;
    if (window.mopub_ad_height == null)
        window.mopub_ad_height = 50;

    var scripts = document.getElementsByTagName('script'),
        script = scripts[scripts.length - 1];
    var mopub_url = document.createElement("a");
    mopub_url.href = script.src;
    
    var mopub_ad_url = "http://"+mopub_url.hostname;
    if (mopub_url.port != "0")
        mopub_ad_url += ":"+mopub_url.port;
    mopub_ad_url += "/m/ad?id="+mopub_ad_unit;

    document.write('<iframe frameborder="0" hspace="0" marginheight="0" marginwidth="0" scrolling="no" vspace="0"'
                   + ' width="'+window.mopub_ad_width+'"'
                   + ' height="'+window.mopub_ad_height+'"'
                   + ' src="'+mopub_ad_url+'">');
    document.write('</iframe>');
})();