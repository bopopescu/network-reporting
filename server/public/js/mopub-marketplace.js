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
            $(this.el + " tr:last").after(renderedContent);
            return this;
        }

    });

    var AdUnitView = Backbone.View.extend({

        initialize: function () {
            this.template = _.template($("#adunit-template").html());
        },

        render: function () {
            var renderedContent = this.template(this.model.toJSON());
            $("tr:last", this.el).after(renderedContent);
            return this;
        }

    });


    window.AdUnit = AdUnit;
    window.AdUnitList = AdUnitList;
    window.App = App;
    window.Inventory = Inventory;
    window.AdUnitView = AdUnitView;
    window.AppView = AppView;


})(this.jQuery, this.Backbone);