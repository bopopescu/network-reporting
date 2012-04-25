(function() {

    var ua = function(browser){
        var agent = navigator.userAgent.toLowerCase();
        return agent.indexOf(browser) !== -1;
    };

    var get_browser = function() {
        if ('msie 7') {
            return 'ie7';
        }

        if ('msie 8') {
            return 'ie8';
        }

        if ('msie 9') {
            return 'ie9';
        }

        if ('msie 10') {
            return 'ie10';
        }

        if ('msie') {
            return 'ie>=6';
        }

        if (ua('opera')) {
            return 'opera';
        }

        if (ua('safari')) {
            if (ua('chrome')) {
                return 'webkit';
            }
            return 'safari';
        } else {
            if (ua('mozilla')) {
                return 'mozilla';
            }
        }

        // leave this one for last because it can appear in
        // non-chrome webkit browsers
        if (ua('chrome')) {
            return 'chrome';
        }

        return 'unorthodox';
    };

    window.Browser = {
        get_browser: get_browser
    };

})();
