/*
	MoPub Client JS
*/
var mopub_click_url;
function redo_tags(div) {
    var at = div.getElementsByTagName('a');
    for (var i=0;i<at.length;i++) {
        var curr = at[i];
        if (curr.href != '#') {
            curr.href = mopub_click_url + '&r=' + encodeURIComponent(curr.href);
        }
        if (window.mopub_click_prepend) {
            curr.href = window.mopub_click_prepend + curr.href;
        }
    }
}

function mp_cb(data) {
    ufid = data.ufid;
    mopub_click_url = data.click_url;
    document.write('<div id="mopub-div-' + ufid + '" style="width:'+window.mopub_ad_width+';height:'+window.mopub_ad_height+'">');
    document.write(data.ad);
    document.write('</div>');

    var div = document.getElementById("mopub-div-"+ufid);
    redo_tags(div);
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
