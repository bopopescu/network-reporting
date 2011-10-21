/*
 * Mopub Marketplace JS
 */

(function($, Backbone) {

    /*
     * AdUnits
     */
    var AdUnit = Backbone.Model.extend({
        defaults : {
            name: "",
            revenue: 0,
            ecpm: 0,
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
        }
    });

    /*
     * Apps/App Inventory
     */

    var App = Backbone.Model.extend({
        defaults : {
            name: "",
            url:"#",
            revenue: 0,
            ecpm: 0,
            attempts: 0,
            impressions: 0,
            fill_rate: 0,
            clicks: 0,
            ctr: 0,
            price_floor: 0,
            app_type: "iOS"
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
        fetchAdUnits: function() {
            this.each(function (app) {
                app.adunits = new AdUnitList();
                app.adunits.app_id = app.id;
                app.adunits.fetch();
            });
        }
    });


    var AppView = Backbone.View.extend({

        initialize: function () {
            this.template = _.template($("#app-template").html());
        },

        render: function () {
            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            var renderedContent = $(this.template(this.model.toJSON()));
            $("a.adunits", renderedContent).click(function(e) {
                e.preventDefault();
                var href = $(this).attr('href').replace("#","");
                Marketplace.fetchAdunitsForApp(href);
            });
            $("tbody", this.el).append(renderedContent);
            return this;
        }
    });

    var AdUnitView = Backbone.View.extend({

        initialize: function () {
            this.template = _.template($("#adunit-template").html());
        },

        render: function () {
            // render the adunit and attach it to the table after it's adunit's row
            var renderedContent = this.template(this.model.toJSON());
            console.log(this.model.get("app_id"));
            var app_row = $("tr#app-" + this.model.get("app_id"), this.el);
            console.log(app_row);
            app_row.after(renderedContent);
            return this;
        }
    });



    var Marketplace = {

        /*
         * Fetches and renders all apps from a list of app_keys.
         * Useful for bootstrapping table loads.
         */
        fetchAllApps: function (app_keys) {
            _.each(app_keys, function(app_key) {
                var app = new App({id: app_key});
                app.bind("change", function(current_app) {
                    var appView = new AppView({ model: current_app, el: "#marketplace_targeting" });
                    appView.render();
                });
                app.fetch();
            });

        },

        /*
         * Fetches and renders all of the adunits from an app key.
         * Useful for showing adunits when a user has clicked on a
         * 'show adunits' link.
         */
        fetchAdunitsForApp: function (app_key) {
            var adunits = new AdUnitList();
            adunits.app_id = app_key;
            adunits.bind("reset", function(adunits_collection) {
                _.each(adunits_collection.models, function(adunit) {
                    var adunitView = new AdUnitView({ model: adunit, el: "#marketplace_targeting" });
                    adunitView.render();
                });
            });
            adunits.fetch();
        }
    };


    // Make everything usable in the page
    window.AdUnit = AdUnit;
    window.AdUnitList = AdUnitList;
    window.App = App;
    window.Inventory = Inventory;
    window.AdUnitView = AdUnitView;
    window.AppView = AppView;
    window.Marketplace = Marketplace;

})(this.jQuery, this.Backbone);