/*
 * # Mopub Marketplace JS
 */

(function($, Backbone) {

    /*
     * ## AdUnit
     */
    var AdUnit = Backbone.Model.extend({
        // If we don't set defaults, the templates will explode
        defaults : {
            attempts: 0,
            clicks: 0,
            ctr: 0,
            ecpm: 0,
            fill_rate: 0,
            impressions: 0,
            name: '',
            price_floor: 0,
            revenue: 0
        },
        validate: function(attributes) {
            var valid_number = Number(attributes.price_floor);
            if (valid_number == NaN) {
                return "please enter a valid number for the price floor";
            }
        }
    });

    /*
     * ## AdUnitCollection
     */
    var AdUnitCollection = Backbone.Collection.extend({
        model: AdUnit,
        url: function() {
            return '/api/app/' + this.app_id + '/adunits/';
        }
    });


    /*
     * ## App
     * We might consider turning derivative values (ecpm, fill_rate, ctr) into
     * functions.
     */
    var App = Backbone.Model.extend({
        defaults : {
            name: '',
            url:'#',
            revenue: 0,
            attempts: 0,
            icon_url: "/placeholders/image.gif",
            impressions: 0,
            fill_rate: 0,
            clicks: 0,
            price_floor: 0,
            app_type: 'iOS',
            ecpm: 0,
            ctr: 0
        },
        url: function () {
            return '/api/app/' + this.id;
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            return response[0];
        }
    });

    /*
     * ## AppCollection
     */
    var AppCollection = Backbone.Collection.extend({
        model: App,
        // If an app key isn't passed to the url, it'll return a list of all of the apps for the account
        url: '/api/app/',
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
            this.template = _.template($('#app-template').html());
        },

        render: function () {
            var renderedContent = $(this.template(this.model.toJSON()));

            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            $('a.adunits', renderedContent).click(showAdUnits).click();
            $('tbody', this.el).append(renderedContent);
            return this;
        }
    });

    /*
     * Utility methods for AppView that control the showing/hiding
     * of adunits underneath an app row.
     */
    function showAdUnits(event){
        event.preventDefault();
        var href = $(this).attr('href').replace('#','');
        Marketplace.fetchAdunitsForApp(href);
        $(this).text('Hide AdUnits').unbind("click").click(hideAdUnits);
    }

    function hideAdUnits(event){
        event.preventDefault();
        var href = $(this).attr('href').replace('#','');
        $.each($(".for-app-" + href), function (iter, item) {
            $(item).remove();
        });
        $(this).text('Show Adunits').unbind("click").click(showAdUnits);
    }

    /*
     * ## AdUnitView
     *
     * See templates/partials/adunit.html to see how this is rendered in HTML
     * Renders an adunit as a row in a table. Also ads the event handler to
     * submit the price floor change over ajax when the price_floor field is changed.
     */
    var AdUnitView = Backbone.View.extend({

        // Define the template
        initialize: function () {
            this.template = _.template($('#adunit-template').html());
        },

        // Render the model in the template. This assumes that the table
        // row for the app has already been rendered. This will render underneath it's
        // app's row.
        render: function () {
            // render the adunit and attach it to the table after it's adunit's row
            var current_model = this.model;
            var renderedContent = $(this.template(this.model.toJSON()));

            // Ad the event handler to submit price floor changes over ajax.
            $('.price_floor_change', renderedContent)
                .change(function() {
                    current_model.set({'price_floor': $(this).val()});
                    current_model.save();
                });
            var app_row = $('tr#app-' + this.model.get('app_id'), this.el);
            app_row.after(renderedContent);
            return this;
        }
    });


    /*
     * ## Marketplace utility methods
     */
    var Marketplace = {

        /*
         * Fetches and renders all apps from a list of app_keys.
         * Useful for bootstrapping table loads.
         */
        fetchAllApps: function (app_keys) {
            _.each(app_keys, function(app_key) {
                var app = new App({id: app_key});
                app.bind('change', function(current_app) {
                    var appView = new AppView({ model: current_app, el: '#marketplace_stats' });
                    appView.render();
                });
                app.fetch({
                    success: function(){
                        $('table').trigger('update');
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
            adunits.bind('reset', function(adunits_collection) {
                _.each(adunits_collection.models, function(adunit) {
                    var adunitView = new AdUnitView({ model: adunit, el: '#marketplace_stats' });
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
     * Globalize everything \o/
     */
    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;
    window.AdUnitView = AdUnitView;
    window.AppView = AppView;
    window.Marketplace = Marketplace;


    /*
     * Boomslam
     */
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

                $('.adunit-row', table).each(function(iter, item) {
                    // find the app row for the adunit
                    var app_id = Marketplace.getAppId(item);
                    var app;
                    if (app_id_cache.hasOwnProperty(app_id)) {
                        app = app_id_cache(app_id);
                    } else {
                        app = $('.app-row#app-' + app_id);
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

        /*
         * Functionality for blocking advertisers from the creatives performance table
         */
        $('a.block').click(function (event) {
            event.preventDefault();
            var block_link = $(this);
            var domain = $(this).attr('id');
            $.ajax({
                type: 'post',
                url: '/campaigns/marketplace/addblocklist',
                data: {
                    blocklist: domain
                },
                success: function (a,b) {
                    block_link.text("Blocked").unbind("click").click(function(){
                        return false;
                    });
                }
            });
        });

        /*
         * Settings page button actions
         */
        $('#settings-submit').click(function(e) {
            e.preventDefault();
            $('#addblocklist').submit();
        });

        $('#blocklist-submit').click(function(e) {
            e.preventDefault();
            $('#addblocklist').submit();
        });


    });

})(this.jQuery, this.Backbone);