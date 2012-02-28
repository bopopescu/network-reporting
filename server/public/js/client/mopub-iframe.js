/*
    MoPub Client JS
*/
var mopub_click_url;
function redo_tags(frame) {
    var a_tags = frame.document.getElementsByTagName('a');
    for (var idx = 0; idx < a_tags.length; idx++) {
        var curr = a_tags[idx];
        if (curr.href != '#') {
            curr.href = mopub_click_url + '&r=' + curr.href;
        }
    }
}

function mp_cb(data) {
    ufid = data.ufid;
    mopub_click_url = data.click_url;
    var iframe = document.getElementById('mopub-iframe-'+ufid);
    iframe = (iframe.contentWindow) ? iframe.contentWindow : (iframe.contentDocument.document);
    iframe.document.open();
    iframe.document.write(data.ad);
    redo_tags(iframe);
    iframe.document.close();
}

function mp_fail() {
   window.location = "mopub://failLoad";
}

(function(){

    function gen_key() {
        var possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz012345678';
        var text = '';
        for( var i=0; i < 20; i++ ) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }

    var c_name = "mopub-udid-cookie";
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
   

    var mopub_site_url = "http://"+mopub_url.hostname;
    if (mopub_url.port != "0")
        mopub_site_url += ":"+mopub_url.port;
    // TODO: add version    
    var ufid = gen_key();
    var mopub_ad_url = mopub_site_url + "/m/ad?id="+mopub_ad_unit + '&ufid=' + ufid;
    if (window.mopub_sha1_udid != null)
        mopub_ad_url += "&udid=sha:" + window.mopub_sha1_udid;
    else
        mopub_ad_url += "&udid=MOBILEWEBCOOKIE:" + get_session();

    if (window.mopub_keywords != null)
        mopub_ad_url += "&q="+escape(window.mopub_keywords);
    mopub_ad_url += '&jsonp=1&callback=mp_cb';

    //iframe for ad
    document.write('<iframe id="mopub-iframe-' + ufid + '" frameborder="0" hspace="0" marginheight="0" marginwidth="0" scrolling="no" vspace="0"'
                   + ' width="'+window.mopub_ad_width+'"'
                   + ' height="'+window.mopub_ad_height+'"'
                   + ' src="about:blank">');
    document.write('</iframe>');
    //init holders for variables
    document.write('<script type="text/javascript" src="'+mopub_ad_url+'"></script>');

    function set_cookie(name, value, expires, path, domain, secure) {
        var cookieString = name + "=" +escape(value) +
        ((expires) ? ";expires=" + expires.toGMTString() : "") +
        ((path) ? ";path=" + path : "") +
        ((domain) ? ";domain=" + domain : "") +
        ((secure) ? ";secure" : "");
        document.cookie = cookieString;
    }

    function get_cookie(name) {
        var start = document.cookie.indexOf(name+"=");
        var len = start+name.length+1;
        if ((!start) && (name != document.cookie.substring(0,name.length))) 
            return null;
        if (start == -1) 
            return null;
        var end = document.cookie.indexOf(";",len);
        if (end == -1) 
            end = document.cookie.length;
        return unescape(document.cookie.substring(len,end));
    }
    
    function get_session() {
        //if no session, set it
        if(!get_cookie(c_name)) {
            set_cookie(c_name, gen_key());
        }
        //get it
        return get_cookie(c_name);
    }

})();
