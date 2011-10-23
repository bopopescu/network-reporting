/*
 * Mopub Marketplace JS
 */

(function($, Backbone) {


    /*
     * # Backbone Models
     *
     * TODO: Refactor these into a mopub models namespace.
     */

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
        },
        validate: function(attributes) {
            var valid_number = Number(attributes.price_floor);
            if (valid_number == NaN) {
                return "please enter a valid number for the price floor";
            }
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


    /*
     * ## AppView
     *
     * See templates/partials/app.html to see how this is rendered in HTML.
     * This renders an app as a table row. It also adds the call to load
     * adunits over ajax and put them in the table.
     */
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
     * ## AdUnitView
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
            var current_model = this.model;
            var renderedContent = $(this.template(this.model.toJSON()));
            $(".price_floor_change", renderedContent).change(function(){
                console.log('yeeeea boiiiii');
                current_model.set({"price_floor": $(this).val()});
                current_model.save();
            });
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
                    var appView = new AppView({ model: current_app, el: "#marketplace_stats" });
                    appView.render();
                });
                app.fetch({
                    success: function(){
                        $("table").trigger("update");
                    }
                });
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
                    var adunitView = new AdUnitView({ model: adunit, el: "#marketplace_stats" });
                    adunitView.render();
                });
            });
            adunits.fetch();
        },

        /*
         * If an adunit row has for-app-[app_id] as a class,
         * strip the app_id and return it. Used for sorting
         * adunit rows underneath their apps.
         */
        getAppId: function(adunit) {
            adunit = $(adunit);

            var app_id = '';
            _.each(adunit.attr('class').split(' '), function(item) {
                if (item.search('for-app-') >= 0) {
                    app_id = item.replace('for-app-', '');
                }
            });

            return app_id;
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

    $(document).ready(function(){

        /*
         * Table sorting doesn't work the way we'd like when adunits have been
         * displayed. We'd like them to sort underneath their apps. Without
         * this formatter function, they sort independently.
         */
        $.tablesorter.addWidget({
            id: 'adunitSorting',
            format: function(table) {
                var app_id_cache = {};

                $(".adunit-row", table).each(function(iter, item) {

                    // find the app row for the adunit
                    var app_id = Marketplace.getAppId(item);
                    var app;
                    if (app_id_cache.hasOwnProperty(app_id)) {
                        app = app_id_cache(app_id);
                    } else {
                        app = $(".app-row#app-" + app_id);
                    }

                    // remove the adunit from it's current location
                    $(item).remove();
                    // and place it after the app row
                    app.after(item);
                });
            }
        });

        $('#marketplace_stats').tablesorter({
            widgets: ['adunitSorting']
        });
    });

})(this.jQuery, this.Backbone);