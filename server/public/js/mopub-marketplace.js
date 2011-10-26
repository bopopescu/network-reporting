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
     * ## Creative
     */
    var Creative = Backbone.Model.extend({
        defaults: {
            revenue: 0,
            ecpm: 0,
            impressions: 0,
            clicks: 0,
            ctr: 0,
            creative_url: "#",
            ad_domain: '#',
            domain_blocked: false
        },
        url: function() {
            return '/api/creative/' +this.id;
        }
    });

    /*
     * ## CreativeCollection
     *
     * This is kind of jankity. Right now creatives are 'collected' by DSP,
     * and its the best way
     */
    var CreativeCollection = Backbone.Collection.extend({
        model: Creative,
        url: function () {
            return '/api/dsp/' + this.dsp_key;
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

        renderInline: function () {
            var app_row = $("tr.app-row#app-" + this.model.id, this.el);
            $(".revenue", app_row).text(this.model.get("revenue"));
            $(".ecpm", app_row).text(this.model.get("ecpm"));
            $(".impressions", app_row).text(this.model.get("impressions"));
            // $(".clicks", app_row).text(this.model.get("clicks"));
            // $(".ctr", app_row).text(this.model.get("ctr"));

            var adunit_show_link = $('a.adunits', app_row);
            adunit_show_link.click(showAdUnits);
            $('a.edit_price_floor', app_row).click(function(e) {
                e.preventDefault();
                adunit_show_link.click();
            });
            return this;
        },
        render: function () {
            var renderedContent = $(this.template(this.model.toJSON()));

            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            $('a.adunits', renderedContent).click(showAdUnits);
            $('tbody', this.el).append(renderedContent);
            return this;
        }
    });


    /*
     * ## CreativeView
     */
    var CreativeView = Backbone.View.extend({
        initialize: function() {
            this.template = _.template($("#creative-row-template").html());
        },

        render: function () {
            var renderedContent = $(this.template(this.model.toJSON()));

            // Here: attach event handlers for stuff in the creative table row

            $("tbody", this.el).append(renderedContent);
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
                    // Save when they click the save button in the price floor cell
                    $(".button", $(this).parent()).click(function() {
                        current_model.save();
                    });
                });

            var app_row = $('tr#app-' + this.model.get('app_id'), this.el);
            var zebra = app_row.hasClass("even") ? "even" : "odd";
            renderedContent.addClass(zebra);

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
        fetchAppStats: function (app_keys) {
            _.each(app_keys, function(app_key) {
                var app = new App({id: app_key});
                app.bind('change', function(current_app) {
                    var appView = new AppView({ model: current_app, el: '#marketplace_stats' });
                    appView.renderInline();
                });
                app.fetch({
                    success: function(){
                        $('table').trigger('update');
                        $("#" + app_key + "-img").hide();
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

            // Once the adunits have been fetched from the server,
            // render them as well as the app's price floor range
            adunits.bind('reset', function(adunits_collection) {

                // Get the max and min price floors from the adunits so
                // we can use them for the app's price floor range
                var high = _.max(adunits_collection.models, function(adunit){
                    return adunit.get("price_floor");
                }).get("price_floor");

                var low = _.min(adunits_collection.models, function(adunit){
                    return adunit.get("price_floor");
                }).get("price_floor");

                // Set the app's price floor to the range of the adunits
                // Keep the "Edit Price Floor" button
                var btn = $("<a href='#" + app_key + "' class='edit_price_floor' id='" + app_key +"'> Edit Price Floor</a>");
                if (high == low) {
                    $(".app-row#app-" + app_key + " .price_floor").html("All $" + high);
                } else {
                    $(".app-row#app-" + app_key + " .price_floor").html("$" + low + " - " + "$" + high);
                }

                // Create the views and render each adunit row
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
        },

        /*
         * Helper method for bootstrapping the creative performance table.
         * Call this method by passing in a list of DSP Keys (see common/constants)
         * and this will load collections of creatives for each dsp.
         */
        fetchAllCreatives: function(dsp_keys) {
            _.each(dsp_keys, function(dsp_key) {

                // Make creative collections for each dsp
                var creative_collection = new CreativeCollection();
                creative_collection.dsp_key = dsp_key;

                // Render all of the creatives on fetch
                creative_collection.bind('reset', function(creatives) {
                    _.each(creatives.models, function (creative) {
                        var creative_view = new CreativeView({model: creative, el: "table#creatives"});
                        creative_view.render();
                    });
                });

                // Fetch the creatives and sort the table (might need to take out the success function)
                creative_collection.fetch({
                    success: function(){
                        $('table#creatives').trigger('update');
                    }
                });
            });

        },

        /*
         * Sends the AJAX request to turn ON the marketplace.
         * This shouldn't just return true, it should return true
         * only when no errors are returned from the server. Fix this.
         */
        turnOn: function() {
            $.ajax({
                type: 'post',
                url: '/campaigns/marketplace/activation/',
                data: {
                    activate: 'on'
                },
            });
            return true;
        },

        /*
         * Sends the AJAX request to turn OFF the marketplace.
         * This shouldn't just return true, it should return true
         * only when no errors are returned from the server. Fix this.
         */
        turnOff: function() {
            $.ajax({
                type: 'post',
                url: '/campaigns/marketplace/activation/',
                data: {
                    activate: 'off'
                },
            });
            return true;
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



    $.fn.pagination = function(options) {
        var defaults = {
            page_length: 10,
            current_page: 0
        };

        var table = $(this);

        table.find('tbody tr').show()
            .lt(currentPage * numPerPage)
            .hide()
            .end()
            .gt((currentPage + 1) * numPerPage - 1)
            .hide()
            .end();

        var numRows = table.find('tbody tr').length;
        var numPages = Math.ceil(numRows / numPerPage);

        var pager = $('<div class="pager"></div>');

        for (var page = 0; page < numPages; page++) {
            $('<span class="page-number">' + (page + 1) + '</span>')
                .appendTo(pager).addClass('clickable');
        }

        // Add the pager after the table
        pager.after(table);
    };


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
            $('').submit();
        });

        $('#blocklist-submit').click(function(e) {
            e.preventDefault();
            $('#addblocklist').submit();
        });

        $("input.targeting-box").click(function() {
            var targeting = $(this).attr('name');
            var activation = $(this).is(":checked") ? "On" : "Off";
            $("label[for='"+ targeting +"']").text(activation);
        });

    });

})(this.jQuery, this.Backbone);