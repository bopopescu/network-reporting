/*
 * Mopub Marketplace JS
 */

(function($, Backbone) {

    /*
     * AdUnit
     */
    var AdUnit = Backbone.Model.extend({
        // If we don't set defaults, the templates will explode
        defaults : {
            name: "",
            revenue: 0,
            attempts: 0,
            impressions: 0,
            fill_rate: 0,
            clicks: 0,
            price_floor: 0,
            ecpm: 0,
            ctr: 0

        },
        ecpm: function() {
            return this.get('revenue')/(this.get('impressions')*1000);
        },
        ctr: function() {
            return (this.get('clicks')/this.get('impressions'))*100;
        }
    });

    /*
     * AdUnitCollection
     */
    var AdUnitCollection = Backbone.Collection.extend({
        model: AdUnit,
        url: function() {
            return '/api/app/' + this.app_id + '/adunits/';
        }
    });


    /*
     * JS Representation of an App.
     * We might consider turning derivative values (ecpm, fill_rate, ctr) into
     * functions.
     */
    var App = Backbone.Model.extend({
        defaults : {
            name: "",
            url:"#",
            revenue: 0,
            attempts: 0,
            impressions: 0,
            fill_rate: 0,
            clicks: 0,
            price_floor: 0,
            app_type: "iOS",
            ecpm: 0,
            ctr: 0
        },
        ecpm: function() {
            return this.get('revenue')/(this.get('impressions')*1000);
        },
        ctr: function() {
            return (this.get('clicks')/this.get('impressions'))*100;
        },
        url: function () {
            return "/api/app/" + this.id;
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            return response[0];
        }
    });


    var AppCollection = Backbone.Collection.extend({
        model: App,
        // If an app key isn't passed to the url, it'll return a list of all of the apps for the account
        url: "/api/app/",
        // Not used anymore, but could come in handy
        fetchAdUnits: function() {
            this.each(function (app) {
                app.adunits = new AdUnitCollection();
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
                $(this).remove();
            });
            $("tbody", this.el).append(renderedContent);
            return this;
        }
    });


    /*
     * AdUnitView
     *
     * See templates/partials/adunit.html to see how this is rendered in HTML
     * The main purpose of this is to render an adunit as a row in a table.
     */
    var AdUnitView = Backbone.View.extend({

        /*
         * Define the template
         */
        initialize: function () {
            this.template = _.template($("#adunit-template").html());
        },

        /*
         * Render the model in the template. This assumes that the table
         * row for the app has already been rendered. This will render after it.
         */
        render: function () {
            // render the adunit and attach it to the table after it's adunit's row
            var renderedContent = this.template(this.model.toJSON());
            var app_row = $("tr#app-" + this.model.get("app_id"), this.el);
            app_row.after(renderedContent);
            return this;
        }
    });


    /*
     * Marketplace utility methods
     */
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
            var adunits = new AdUnitCollection();
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


    /*
     * Globalize everything 8)
     */
    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;
    window.AdUnitView = AdUnitView;
    window.AppView = AppView;
    window.Marketplace = Marketplace;

})(this.jQuery, this.Backbone);