/*
	MoPub Client JS
*/
(function(){
    if (typeof window.mopub_ad_unit == 'undefined') {
        console.log("MoPub load failed. mopub_ad_unit needs to be defined.");
        return;
    }
    
    if (window.mopub_ad_width == null)
        window.mopub_ad_width = 320;
    if (!window.mopub_ad_height == null)
        window.mopub_ad_height = 50;

    document.write('<iframe frameborder="0" hspace="0" marginheight="0" marginwidth="0" scrolling="no" vspace="0"'
                   + ' width="'+window.mopub_ad_width+'"'
                   + ' height="'+window.mopub_ad_height+'"'
                   + ' src="http://ads.mopub.com/m/ad?id=' + mopub_ad_unit+'">');
    document.write('</iframe>');
})();