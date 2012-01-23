/*
 * # Mopub Marketplace JS
 */
var mopub = mopub || {};

// depends underscore, backbone, jquery, mopub.chart, mopub.util
(function($, Backbone, _) {

    /*
     * ## AdUnit
     */
    var AdUnit = Backbone.Model.extend({
        // If we don't set defaults, the templates will explode
        defaults : {
            active: false,
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
        calcCtr: function () {
            return (this.get('clicks') / (this.get('impressions')+1));
        },
        calcEcpm: function () {
            return (this.get('revenue') / (this.get('impressions')+1)*1000);
        },
        calcFillRate: function () {
            if (attempts === 0) {
                return 0.0;
            }
            return (impressions/attempts)*100;
        },
        validate: function(attributes) {
            if (typeof(attributes.price_floor) != 'undefined') {
                var valid_number = Number(attributes.price_floor);
                if (isNaN(valid_number)) {
                    return "Please enter a valid number for the price floor";
                }
            }
        },
        url: function() {
            return '/api/app/' + this.app_id + '/adunits/' + this.id + '?' + window.location.search.substring(1);
        }
    });

    /*
     * ## AdUnitCollection
     */
    var AdUnitCollection = Backbone.Collection.extend({
        model: AdUnit,
        url: function() {
            return '/api/app/' + this.app_id + '/adunits/?' + window.location.search.substring(1);
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
            return '/api/app/' + this.id + "?"  + window.location.search.substring(1);
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
            return '/api/creative/' + this.id + "?" +  window.location.search.substring(1);
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
            return '/api/dsp/' + this.dsp_key + "?" + window.location.search.substring(1);
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
            $(".revenue", app_row).text(mopub.Utils.formatCurrency(this.model.get("revenue")));
            $(".impressions", app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $(".ecpm", app_row).text(mopub.Utils.formatCurrency(this.model.get("ecpm")));
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
     * ## showAdUnits/hideAdUnits
     *
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
        $("#app-" + href + " a.view_targeting").removeClass("hidden");
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

        initialize: function () {
            this.template = _.template($('#adunit-template').html());
        },

        /*
         * Render the AdUnit into a table row that already exists. Adds handlers
         * for changing AdUnit attributes over ajax.
         */
        renderInline: function () {
            var current_model = this.model;
            var adunit_row = $("tr.adunit-row#adunit-" + this.model.id, this.el);

            $(".revenue", adunit_row).text(mopub.Utils.formatCurrency(this.model.get("revenue")));
            $(".ecpm", adunit_row).text(mopub.Utils.formatCurrency(this.model.get("ecpm")));
            $(".impressions", adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $(".price_floor", adunit_row).html('<img class="loading-img hidden" src="/images/icons-custom/spinner-12.gif"></img> ' +
                                               '<input id="' +
                                               this.model.id +
                                               '" type="text" class="input-text input-text-number number" style="width:50px;margin: -3px 0;" value="' +
                                               this.model.get("price_floor") +
                                               '"> ');
            $(".targeting", adunit_row).html('<img class="loading-img hidden"  src="/images/icons-custom/spinner-12.gif"></img> ' +
                                             '<input class="targeting-box" type="checkbox">');

            if (this.model.get("active")) {
                $("input.targeting-box", adunit_row).attr('checked', 'checked');
            }

            // Add the event handler to submit targeting changes over ajax.
            $("input.targeting-box", adunit_row).click(function() {
                var loading_img = $(".targeting .loading-img", adunit_row);
                loading_img.show();
                var is_valid = current_model.save({'active': $(this).is(":checked")}, {
                    success: function (model, response) {
                        setTimeout(function() {
                            loading_img.hide();
                        }, 2000);
                    }
                });
            });

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor .input-text', adunit_row).keyup(function() {
                var input_field = $(this);
                input_field.removeClass('error');
                var loading_img = $(".price_floor .loading-img", adunit_row);
                loading_img.show();

                var promise = current_model.save({
                    price_floor: $(this).val()
                });
                if (promise) {
                    promise.success(function() {
                        loading_img.hide();
                    });
                    promise.error(function() {
                        loading_img.hide();
                    });
                } else {
                    loading_img.hide();
                    input_field.addClass('error');
                }
            });

            return this;
        },

        /*
         * Render the adunit model in the template. This assumes that the table
         * row for the app has already been rendered. This will render underneath
         * it's app's row.
         */
        render: function () {
            // render the adunit and attach it to the table after it's adunit's row
            var current_model = this.model;
            var renderedContent = $(this.template(this.model.toJSON()));

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor_change', renderedContent)
                .change(function() {
                    current_model.set({'price_floor': $(this).val()});
                    // Save when they click the save button in the price floor cell
                    var save_link = $(".save", $(this).parent());
                        save_link.click(function(e) {
                            e.preventDefault();
                            save_link.addClass('disabled').text('Saving...');
                            current_model.save({}, {
                                success: function () {
                                    setTimeout(function() {
                                        save_link.removeClass('disabled').text('Saved');
                                        save_link.text("Save");
                                    }, 2000);
                                }
                            });
                        });
                });

            // Add the event handler to submit targeting changes over ajax.
            $("input.targeting-box", renderedContent).click(function() {
                var targeting = $(this).attr('name');
                var activation = $(this).is(":checked") ? "On" : "Off";
                $("label[for='"+ targeting +"']", renderedContent).text(activation);

                current_model.set({'active': $(this).is(":checked")});
                current_model.save();
            });

            // Add the right background color based on where the app is in the table
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

    /*
     * Fetches and renders all apps from a list of app_keys.
     * Useful for bootstrapping table loads.
     */
    function fetchAllApps (app_keys) {
        _.each(app_keys, function(app_key) {
            var app = new App({ id: app_key, stats_endpoint: 'mpx' });
            app.bind('change', function(current_app) {
                var appView = new AppView({ model: current_app, el: 'marketplace-apps' });
                appView.render();
            });
            app.fetch({
                success: function(){
                    $('table').trigger('update');
                }
            });
        });
    }

    /*
     * Fetches all app stats using a list of app keys and renders
     * them into table rows that have already been created in the
     * page. Useful for decreasing page load time along with `fetchAdunitStats`.
     */
    function fetchAppStats (app_keys) {
        _.each(app_keys, function(app_key) {
            var app = new App({id: app_key, stats_endpoint: 'mpx'});
            app.bind('change', function(current_app) {
                var appView = new AppView({ model: current_app, el: 'marketplace-apps' });
                appView.renderInline();
            });
            app.fetch();
        });
    }

    /*
     * Fetches AdUnit stats over ajax and renders them in already existing table rows.
     * This method is useful for decreasing page load time. Uses a parent app's key
     * to bootstrap the fetch.
     */
    function fetchAdunitStats (app_key, marketplace_active) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;
        adunits.stats_endpoint = 'mpx';
        // Once the adunits have been fetched from the server,
        // render them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {
            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                adunit.app_id = app_key;
                var adunitView = new AdUnitView({ model: adunit, el: '#marketplace_stats' });
                adunitView.renderInline();
            });
        });

        adunits.fetch({
            success: function(){
                // Trigger any event handlers that have been attached to the table.
                // Shouldn't this only trigger for the table that the adunit stats are
                // being placed in?
                $('table').trigger('update');
                $("#" + app_key + "-img").hide();
                if (!marketplace_active) {
                    $(".targeting-box").attr('disabled', true);
                }
            }
        });
    }

    /*
     * Fetches and renders all of the adunits from an app key.
     * Useful for showing adunits when a user has clicked on a
     * 'show adunits' link.
     */
    function fetchAdunitsForApp (app_key) {
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

            // Set the app's price floor cell to the range of the adunits
            // Keep the "Edit Price Floor" button
            var btn = $("<a href='#" + app_key +"'" +
                        " class='edit_price_floor' " +
                        "id='" + app_key + "'> "
                        + "Edit Price Floor</a>");

            if (high == low) {
                $(".app-row#app-" + app_key + " .price_floor").html("All $" + high);
            } else {
                $(".app-row#app-" + app_key + " .price_floor").html("$" + low + " - " + "$" + high);
            }

            // Disable the 'view' link in the app row under the targeting column
            $(".app-row#app-" + app_key + " .view_targeting").addClass("hidden");

            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                var adunitView = new AdUnitView({ model: adunit, el: 'marketplace-apps' });
                adunitView.render();
            });
        });

         adunits.fetch();
    }

    /*
     * If an adunit row has for-app-[app_id] as a class,
     * strip the app_id and return it. Used for sorting
     * adunit rows underneath their apps.
     */
    function getAppId (adunit) {

        adunit = $(adunit);
        var app_id = '';
        var adunit_classes = adunit.attr('class').split(' ');

        _.each(adunit_classes, function(adunit_class) {
            if (adunit_class.search('for-app-') >= 0) {
                app_id = adunit_class.replace('for-app-', '');
            }
        });

        return app_id;
    }

    /*
     * Sends the AJAX request to turn ON the marketplace.
     * This shouldn't just return true, it should return true
     * only when no errors are returned from the server. Fix this.
     */
    function turnOn () {
        var on = $.post('/campaigns/marketplace/activation/', {
            activate: 'true'
        });

        on.error(function() {
            Toast.error("There was an error saving your Marketplace settings. Please try again soon.");
        });

        on.done(function() {
            //Toast.success("Foo.");
        });

        $(".targeting-box").removeAttr('disabled');
        $("#blindness").removeAttr('disabled');
        return true;
    }

    /*
     * Sends the AJAX request to turn OFF the marketplace.
     * This shouldn't just return true, it should return true
     * only when no errors are returned from the server. Fix this.
     */
    function turnOff () {
        var off = $.post('/campaigns/marketplace/activation/', {
            activate: 'false'
        });
        $(".targeting-box").attr('disabled', true);
        $("#blindness").attr('disabled', true);
        return true;
    }

    /*
     * Makes the Creatives Performance tab's datatable
     */
    function makeCreativePerformanceTable (pub_id, blocklist, start_date, end_date) {
        var creative_data_url = window.location.origin + "/campaigns/marketplace/creatives/";
        var table = $("#report-table").dataTable({
            bProcessing: true,
            // Use jQueryUI to style the table
            bJQueryUI: true,
            // Add page numbers to the table instead of just prev/next buttons
            sPaginationType: "full_numbers",
            // Message that appears when the table is empty
            oLanguage: {
                sEmptyTable: "No creatives have been displayed for this time range."
            },
            // Column Width
            aoColumns:[
                {sWidth: "330px"}, // Creative iFrame
                {sWidth: "190px"}, // Advertiser
                {sWidth: "120px"}, // Revenue
                {sWidth: "90px"},  // eCPM
                {sWidth: "90px"}   // Impressions
                //{"sWidth": "80px"}, // Clicks
                //{"sWidth": "80px"}, // CTR
            ],
            // Don't resize table columns automatically, we'll do it manually
            bAutoWidth:false,
            // Sort by revenue descending on table load
            aaSorting: [[2,'desc']],
            // Endpoint to fetch table data
            sAjaxSource: creative_data_url,
            // Tell datatables how to fetch and parse server data
            fnServerData: function( sUrl, aoData, fnCallback ) {
                $.ajax({
                    url: sUrl,
                    data: {
                        pub_id: pub_id,
                        start: start_date,
                        end: end_date,
                        format:'jsonp'
                    },
                    // When the data returns from the endpoint, we have to format it the way
                    // datatables wants. We also have to make sure to get the types of each
                    // data the way we want them if we want sorting to work correctly.
                    success: function(data, textStatus, jqXHR) {

                        var creative_data = _.map(data, function(creative, key) {
                            var ecpm = (creative['stats']['pub_rev'] / (creative['stats']['imp']+1))*1000;
                            return [
                                creative["creative"]["url"],
                                creative["creative"]["ad_dmn"],
                                creative["stats"]["pub_rev"].toFixed(2),
                                creative["stats"]["imp"],
                                ecpm
                            ];
                        });

                        var response = {
                            aaData: creative_data
                        };
                        fnCallback(response, textStatus, jqXHR);
                    },
                    dataType: "jsonp",
                    cache: false
                } );
            },
            // Callback function that takes table data and renders it
            // as a table row. Called on each row's data right before
            // it's rendered in the table (i.e. when a user clicks
            // 'next'/'prev', or changes the number of displayed rows)
            fnRowCallback: function(nRow, aData, iDisplayIndex) {

                $("td:eq(0)", nRow).html("<iframe width='320px' height='50px' src='" +
                                         aData[0] +
                                         "'></iframe>");

                var domain = aData[1];
                if (_.contains(blocklist, domain)) {
                    $("td:eq(1)", nRow).text(domain + " (Blocked)");
                } else if (domain != null) {
                    // Please leave this commented. This feature will be uncommented and used
                    // in the future. Thanks.
                    // var anchor = $("<a href='#'> Block </a>").click(function (event) {
                    //     var $this = $(this);
                    //     event.preventDefault();
                    //     var blocklist_xhr = $.post("/campaigns/marketplace/settings/blocklist/", {
                    //         action: 'add',
                    //         blocklist: domain
                    //     });
                    //     blocklist_xhr.done(function() {
                    //         $this.parent().append(' (Blocked)');
                    //         $this.remove();
                    //     });
                    // });
                    $("td:eq(1)", nRow).html(domain);
                } else {
                    $("td:eq(1)", nRow).html("<span class='muted'>(Unknown)</span>");
                }
                $("td:eq(2)", nRow).addClass("numeric").text("$" + mopub.Utils.formatNumberWithCommas(aData[2]));
                $("td:eq(3)", nRow).addClass("numeric").text(mopub.Utils.formatNumberWithCommas(aData[3]));
                $("td:eq(4)", nRow).addClass("numeric").text(mopub.Utils.formatCurrency(aData[4]));
                return nRow;
            }
        });

        return table;
    }

    /*
     * Adds a domain to the in=page blocklist, along with an
     * anchor + click event to remove it over Ajax.
     */
    function addToBlocklist (domain) {
        var anchor = $("<a href='#'>Remove</a>").click(blocklistRemoveClickHandler);
        var list_item = $("<li></li>").html(domain + " ");
        list_item.append(anchor);
        $("#blocked_domains").append(list_item);
    }

    function blocklistRemoveClickHandler (event) {
        event.preventDefault();

        var anchor = $(this);
        var domain = anchor.attr('id');
        $("img", anchor.parent()).removeClass('hidden');
        var blocklist_xhr = $.post("/campaigns/marketplace/settings/blocklist/", {
            action: 'remove',
            blocklist: domain
        });

        blocklist_xhr.done(function (response) {
            $("img#" + domain).addClass('hidden');
            anchor.parent().fadeOut();
        });

        blocklist_xhr.error(function (response) {
            $("img#" + domain).addClass('hidden');
            Toast.error(response);
        });
    }



    var MarketplaceController = {
        initializeIndex: function (bootstrapping_data) {

            // Fill in the stats data for each of the apps and
            // each of their adunits
            fetchAppStats(bootstrapping_data.app_keys);
            _.each(bootstrapping_data.app_keys, function(app_key) {
                fetchAdunitStats(app_key, bootstrapping_data.marketplace_active);
            });

            var table = makeCreativePerformanceTable(bootstrapping_data.pub_key,
                                                     bootstrapping_data.blocklist,
                                                     bootstrapping_data.start_date,
                                                     bootstrapping_data.end_date);

            /*
             * Blindness settings
             */
            $("#blindness").click(function () {
                var loading_img = $("#blindness-spinner").show();
                var saving = $("#blindness-save-status .saving").show();

                var blindness_xhr = $.post("/campaigns/marketplace/settings/blindness/",{
                    activate: $(this).is(":checked")
                });

                blindness_xhr.done(function(data){
                    loading_img.hide();
                    saving.hide();
                    if (data.hasOwnProperty('success')) {
                        var saved = $("#blindness-save-status .saved").show();
                        setTimeout(function() { saved.fadeOut(); }, 1000);
                    } else {
                        var errored = $("#blindness-save-status .error").show();
                        setTimeout(function() {errored.fadeOut(); }, 1000);
                    }
                });
            });

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

            /*
             * Set up the marketplace table. By default we're going to sort by app name.
             * Icons (header 0), price floors (header 6) and targeting (header 7) columns
             * can't be sorted because that just doesn't make sense fool.
             */
            // $('marketplace-apps').tablesorter({
            //     widgets: ['adunitSorting'],
            //     sortList: [[1, 0]],
            //     headers: { 0: { sorter: false}, 6: {sorter: false}, 7: {sorter: false} }
            // });

            /*
             * Functionality for blocking advertisers from the creatives performance table
             */
            $('a.block').click(function (event) {
                event.preventDefault();
                var block_link = $(this);
                var domain = $(this).attr('id');
                $.ajax({
                    type: 'post',
                    url: '/campaigns/marketplace/settings/blocklist/',
                    data: {
                        blocklist: domain,
                        action: "add"
                    },
                    success: function (a,b) {
                        block_link.text("Blocked").unbind("click").click(function(){
                            return false;
                        });
                    }
                });
            });

            /*
             * Make the lightswitches turn the Marketplace on and off.
             * They're all bound to the same selector so that any time someone
             * clicks the Marketplace On/Off switch, all of them get turned off.
             */
            $(".lightswitch").lightswitch(turnOn, turnOff);

            /*
             * Toasts for the top and bottom lightswitches. Toasts are little flash messages
             * that let the user know something has happened. These should be rolled up
             * into their own library and put in mopub.js. For now they're here because
             * this is the only place they're used.
             *
             * # REFACTOR: use the new kind of toast
             */
            $("#top_switch").click(function() {
                if ( $("#top_switch .switch").hasClass('on') ) {
                    $("#first_time_toast").fadeIn();
                    setTimeout(function() {
                        $("#first_time_toast").fadeOut();
                    }, 3000);
                }
            });

            $("#bottom_switch").click(function() {
                if ( $("#bottom_switch .switch").hasClass('off') ) {
                    $("#settings_toast").fadeIn();
                    setTimeout(function() {
                        $("#settings_toast").fadeOut();
                    }, 3000);
                }
            });

            /*
             * ## Blocklist adding/editing
             * Click/form handlers and ajax stuff for the blocklist
             * in the settings tab
             */
            $('#blocklist-submit').click(function(e) {
                e.preventDefault();
                var blocklist = $("textarea[name='blocklist']").val();
                var blocklist_xhr = $.post('/campaigns/marketplace/settings/blocklist/', {
                    action: 'add',
                    blocklist: blocklist
                });

                blocklist_xhr.done(function (response) {
                    var domains = response['new'];
                    $.each(domains, function(iter, domain) {
                        addToBlocklist(domain);
                    });
                    $("textarea[name='blocklist']").val('');
                });

                blocklist_xhr.error(function (response) {
                    Toast.warning(response);
                });
            });

            /*
             * ## Blocklist removal
             */
            $("a.blocklist_remove").click(blocklistRemoveClickHandler);

            /*
             * ## Content filtering
             */

            $("input.content_level").click(function(){
                var self = $(this);
                var filter_level = self.attr('value');
                var loading_img = $("#filter-spinner").show();
                var saving = $("#filter-save-status .saving").show();
                var result = $.post("/campaigns/marketplace/settings/content_filter/", {
                    filter_level: filter_level
                });
                result.success(function(data){
                    loading_img.hide();
                    saving.hide();
                    if (data.hasOwnProperty('success')) {
                        var saved = $("#filter-save-status .saved").show();
                        setTimeout(function() { saved.fadeOut(); }, 1000);

                    } else {
                        var errored = $("#filter-save-status .error").show();
                        setTimeout(function() {errored.fadeOut(); }, 1000);
                    }
                });
            });




            /*
             * F THIS.
             * REFACTOR.
             *
             * Everything here and below needs to not exist in this file, because
             * it already exists in two other files. Obvo refactor.
             */
            function getCurrentChartSeriesType() {
                var activeBreakdownsElem = $('#dashboard-stats .stats-breakdown .active');
                if (activeBreakdownsElem.attr('id') == 'stats-breakdown-ecpm') return 'line';
                else return 'area';
            }

            $('.stats-breakdown tr').click(function(e) {
                $('#dashboard-stats-chart').fadeOut(100, function() {
                    mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
                    $(this).show();
                });
            });

            var dailyStats = mopub.accountStats["daily"];
            mopub.dashboardStatsChartData = {
                pointStart: mopub.graphStartDate,
                pointInterval: 86400000,
                revenue: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "revenue_float")}],
                impressions: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "impressions")}],
                ecpm: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "ecpm_float")}]
            };
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());

            // set up dateOptions
            $('#dashboard-dateOptions input').click(function() {
                var option = $(this).val();
                var hash = document.location.hash;
                if(option == 'custom') {
                    $('#dashboard-dateOptions-custom-modal').dialog({
                        width: 570,
                        buttons: [
                            {
                                text: 'Set dates',
                                css: { fontWeight: '600' },
                                click: function() {
                                    var from_date=$('#dashboard-dateOptions-custom-from').datepicker("getDate");
                                    var to_date=$('#dashboard-dateOptions-custom-to').datepicker("getDate");
                                    var num_days=Math.ceil((to_date.getTime()-from_date.getTime())/(86400000)) + 1;

                                    var from_day=from_date.getDate();
                                    var from_month=from_date.getMonth()+1;
                                    var from_year=from_date.getFullYear();

                                    $(this).dialog("close");
                                    var location = document.location.href.replace(hash, '').replace(/\?.*/,'');
                                    document.location.href = location +
                                        '?r=' + num_days +
                                        '&s=' + from_year + "-" + from_month + "-" + from_day +
                                        hash;
                                }
                            },
                            {
                                text: 'Cancel',
                                click: function() {
                                    $(this).dialog("close");
                                }
                            }
                        ]
                        });
                } else {
                    // Tell server about selected option to get new data
                    var location = document.location.href.replace(hash,'').replace(/\?.*/,'');
                    document.location.href = location+'?r=' + option + hash;
                }
            });

            // set up stats breakdown dateOptions
            $('#stats-breakdown-dateOptions input').click(function() {
                $('.stats-breakdown-value').hide();
                $('.stats-breakdown-value.'+$(this).val()).show();
            });

            // set up custom dateOptions modal dialog
            $('#dashboard-dateOptions-custom-from').datepicker({
                defaultDate: '-15d',
                maxDate: '0d',
                onSelect: function(selectedDate) {
                    var other = $('#dashboard-dateOptions-custom-to');
                    var instance = $(this).data("datepicker");
                    var date = $.datepicker
                        .parseDate(instance.settings.dateFormat ||
                                   $.datepicker._defaults.dateFormat,
                                   selectedDate,
                                   instance.settings);
                    other.datepicker('option', 'minDate', date);
                }
            });
            $('#dashboard-dateOptions-custom-to').datepicker({
                defaultDate: '-1d',
                maxDate: '0d',
                onSelect: function(selectedDate) {
                    var other = $('#dashboard-dateOptions-custom-from');
                    var instance = $(this).data("datepicker");
                    var date = $.datepicker
                        .parseDate(instance.settings.dateFormat ||
                                   $.datepicker._defaults.dateFormat,
                                   selectedDate,
                                   instance.settings);
                    other.datepicker('option', 'maxDate', date);
                }
            });

        }
    };

    window.MarketplaceController = MarketplaceController;

})(this.jQuery, this.Backbone, this._);
