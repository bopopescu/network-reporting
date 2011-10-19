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
        }
    });

    var AdUnitList = Backbone.Collection.extend({
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
        model: App,
        url: "/api/app/",
        parse: function(response) {
            return response.apps;
        }
    });

    window.AdUnit = AdUnit;
    window.AdUnitList = AdUnitList;
    window.App = App;
    window.Inventory = Inventory;

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

        var inventory = new Inventory();
        inventory.fetch({
            success: logInventory
        });
        function logInventory (inventory, options) {
            inventory.each(function (app) {
                console.log(app.get('name'));
                window.guy = app;
            });
        }
    });

})(this.jQuery, this.Backbone);