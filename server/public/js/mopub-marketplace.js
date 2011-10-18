/*
 * Mopub Marketplace JS
 */

(function($, Backbone) {

    var AdUnit = Backbone.Model.extend({
        defaults : {
            revenue: 0,
            eCPM: 0,
            attempts: 0,
            impressions: 0,
            fill_rate: 0,
            clicks: 0,
            ctr: 0,
            price_floor: 0
        },
        initialize: function() {
            console.log('adunit initialized');
        }
    });

    var AdGroup = Backbone.Collection.extend({
        model: AdUnit
    });

    var App = Backbone.Model.extend({
        defaults : {
            revenue: 0,
            eCPM: 0,
            attempts: 0,
            impressions: 0,
            fill_rate: 0,
            clicks: 0,
            ctr: 0
        }
    });

    var Inventory = Backbone.Collection.extend({
        model: App
    });

    $(document).ready(function() {

        $(".lightswitch").lightswitch();

        /*
         * Show/hide adunits in the table under the performance tab
         */
        $("a.adunits").click(function() {
            var href = $(this).attr('href').replace("#","");
            console.log(href);
            $(".adunit-data-" + href).each(function () {
                if ($(this).hasClass('hidden')) {
                    $(this).slideUp().removeClass('hidden');
                } else {
                    $(this).slideDown().addClass('hidden');
                }
            });

        });
    });

})(this.jQuery, this.Backbone);