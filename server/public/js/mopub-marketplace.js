/*
 * Mopub Marketplace JS
 */

(function($, Backbone) {

    /*
     * AdUnits
     */
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
        model: AdUnit,
        url: function() {
            return '/api/app/' + this.app_id + '/adunits/';
        },
        parse: function (response) {
            return response.adunits;
        },
        initialize: function() {
            var self = this;

            self.bind("reset", function(collection) {
                collection.each(function (adunit) {
                    console.log(adunit.get("name"));
                });
            });
        }
    });

    /*
     * Apps/App Inventory
     */

    var App = Backbone.Model.extend({
        defaults: {
            adunits: []
        },
        url: function () {
            return "/api/app/" + this.id;
        },
        parse: function (response) {
            return response.apps[0];
        }
    });


    var Inventory = Backbone.Collection.extend({
        model: App,

        // If an app key isn't passed to the url, it'll return a list of all of the apps for the account
        url: "/api/app/",

        parse: function(response) {
            return response.apps;
        },

        initialize: function() {
            var self = this;

            // When the collection is fetched or reset, fetch all of the
            // adunits for each of the apps
            self.bind("reset", function(collection) {
                collection.each(function (app) {
                    console.log(app.get("name"));
                    app.adunits = new AdUnitList();
                    app.adunits.app_id = app.id;
                    app.adunits.fetch();
                });
            });
        }
    });


    /*
     * Views
     */

    var MarketplaceAppRow = Backbone.View.extend({
        tagName: "tr"
    });

    var MarketplaceTargetingTable = Backbone.View.extend({
        el: $("#marketplace_targeting"),
        tagName: 'table',
        id:"marketplace_targeting",

        initialize: function() {
            var inventory = new Inventory();
            inventory.fetch();
        }
    });

    var Rollup = Backbone.View.extend({
       className: "rollup",
    });

    window.AdUnit = AdUnit;
    window.AdUnitList = AdUnitList;
    window.App = App;
    window.Inventory = Inventory;

    window.MarketplaceTargetingTable = MarketplaceTargetingTable;

})(this.jQuery, this.Backbone);