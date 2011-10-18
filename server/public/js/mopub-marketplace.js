/*
 * Mopub Marketplace JS
 */

(function($) {

    /*
     * lightswitch takes two functions, an on function and an off function.
     * When the lightswitch in the page is clicked on or off, the the corresponding
     * function is called. If the function returns true, the switch is slid.
     *
     * Usage:
     *
     * var on = function() {
     *    console.log('BOOMSLAM');
     *    return true;
     * };
     *
     * var off = function() {
     *    console.log('SEE YA');
     *    return true;
     * };
     *
     * $(".lightswitch").lightswitch(on, off);
     */
    $.fn.lightswitch = function (on_function, off_function) {

        if (typeof on_function == 'undefined') {
            on_function = function () {
                return true;
            };
        }

        if (typeof off_function == 'undefined') {
            off_function = function () {
                return true;
            };
        }

        var light_switch = $(this);
        var switcher = $('.switch', light_switch);

        light_switch.click(function () {
            if (switcher.hasClass('on')) {
                var result = off_function();
                if (result) {
                    switcher.removeClass('on').addClass('off');
                }

            } else if (switcher.hasClass('off')) {
                var result = on_function();
                if (result) {
                    switcher.removeClass('off').addClass('on');
                }
            } else {
                switcher.addClass('off');
            }
        });
    };

    $(document).ready(function() {
        var on = function() {
            console.log('BOOMSLAM');
            return true;
        };

        var off = function() {
            console.log('SEE YA');
            return true;
        };

        $(".lightswitch").lightswitch(on, off);
    });

})(this.jQuery);