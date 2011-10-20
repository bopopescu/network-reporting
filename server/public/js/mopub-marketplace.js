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
        },
        initialize: function() {
            var self = this;
            self.bind('reset', function() {

            });
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
            });
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
        initialize: function() {
            var self = this;

            // When the collection is fetched or reset, fetch all of the
            // adunits for each of the apps
            self.bind("reset", function(collection) {
                //this.fetchAdUnits();
            });
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
            var renderedContent = this.template(this.model.toJSON());
            $("tbody", this.el).append(renderedContent);
            return this;
        }
    });

    var AdUnitView = Backbone.View.extend({

        initialize: function () {
            this.template = _.template($("#adunit-template").html());
        },

        render: function () {
            var renderedContent = this.template(this.model.toJSON());
            $("#app", this.el).append(renderedContent);
            return this;
        }

    });


    window.AdUnit = AdUnit;
    window.AdUnitList = AdUnitList;
    window.App = App;
    window.Inventory = Inventory;
    window.AdUnitView = AdUnitView;
    window.AppView = AppView;


    var Marketplace = {

        fetchAllApps: function (app_keys) {
            _.each(app_keys, function(app_key) {
                var app = new App({id: app_key});
                app.bind("change", function(current_app) {
                    var appView = new AppView({model: current_app, el: "#marketplace_targeting"});
                    appView.render();
                });
                app.fetch();
            });
        },

        fetchAllAdUnits: function (adunit_keys) {
            _.each(adunit_keys, function(adunit_key) {
                var adunit = new AdUnit({id: adunit_key});
                adunit.bind("change", function(current_adunit) {
                    var adunitView = new AdUnitView({model: current_adunit, el: "#marketplace_targeting"});
                    adunitView.render();
                });
                adunit.fetch();
            });
        }

    };


    window.Marketplace = Marketplace;

    $(document).ready(function() {
        $("a.adunits").click(function() {
            var href = $(this).attr('href').replace("#","");
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