/*
 * # Mopub Marketplace JS
 */
var mopub = mopub || {};

// depends underscore, backbone, jquery, mopub.chart, mopub.util
(function($, _) {

    /*
     * ## Marketplace utility methods
     */

    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    /*
     * Fetches all app stats using a list of app keys and renders
     * them into table rows that have already been created in the
     * page. Useful for decreasing page load time along with `fetchAdunitsFromAppKey`.
     */
    function fetchAppsFromKeys (app_keys) {
        var apps = new AppCollection();
        var fetched_apps = 0;

        _.each(app_keys, function(app_key) {
            var app = new App({id: app_key, stats_endpoint: 'mpx'});
            app.bind('change', function(current_app) {
                var appView = new AppView({
                    model: current_app,
                    el: 'marketplace-apps'
                });
                appView.renderInline();
            });

            app.fetch({
                error: function () {
                    app.fetch({
                        error: toast_error
                    });
                },
                success: function() {
                    fetched_apps++;
                    if (fetched_apps == app_keys.length) {
                        apps.trigger('loaded');
                    }
                }
            });

            apps.add(app);
        });

        return apps;
    }

    /*
     * Fetches AdUnit stats over ajax and renders them in already
     * existing table rows.  This method is useful for decreasing page
     * load time. Uses a parent app's key to bootstrap the fetch.
     */
    function fetchAdunitsFromAppKey (app_key, marketplace_active) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;
        adunits.stats_endpoint = 'mpx';
        // Once the adunits have been fetched from the server,
        // render them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {
            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                adunit.app_id = app_key;
                var adunitView = new AdUnitView({
                    model: adunit,
                    el: '#marketplace_stats'
                });
                adunitView.renderInline();
            });
        });
        adunits.fetch({
            success: function(){
                // Trigger any event handlers that have been attached
                // to the table.  Shouldn't this only trigger for the
                // table that the adunit stats are being placed in?
                $('table').trigger('update');
                $("#" + app_key + "-img").hide();
                if (!marketplace_active) {
                    $(".targeting-box").attr('disabled', true);
                }
            },
            error: function () {
                adunits.fetch({
                    error: toast_error
                });
            }
        });
    }

    /*
     * Fetches and renders all of the adunits from an app key.  Useful
     * for showing adunits when a user has clicked on a 'show adunits'
     * link.
     */
    function fetchAdunitsForApp (app_key) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;

        // Once the adunits have been fetched from the server, render
        // them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {

            // Get the max and min price floors from the adunits so we
            // can use them for the app's price floor range
            var high = _.max(adunits_collection.models, function(adunit){
                 return adunit.get("price_floor");
            }).get("price_floor");

            var low = _.min(adunits_collection.models, function(adunit){
                return adunit.get("price_floor");
            }).get("price_floor");

            // Set the app's price floor cell to the range of the
            // adunits Keep the "Edit Price Floor" button
            var btn = $("<a href='#" + app_key +"'" +
                        " class='edit_price_floor' " +
                        "id='" + app_key + "'> "
                        + "Edit Price Floor</a>");

            // Display the range of price floors for the app. (This is
            // no longer used, but left in because it could be used
            // again in the future).
            if (high == low) {
                $(".app-row#app-" + app_key + " .price_floor").html("All $" + high);
            } else {
                $(".app-row#app-" + app_key + " .price_floor").html("$" + low + " - " + "$" + high);
            }

            // Disable the 'view' link in the app row under the targeting column
            $(".app-row#app-" + app_key + " .view_targeting").addClass("hidden");

            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                var adunitView = new AdUnitView({
                    model: adunit,
                    el: 'marketplace-apps'
                });
                adunitView.render();
            });
        });

         adunits.fetch({
             error: function() {
                 adunits.fetch({
                     error: toast_error
                 });
             }
         });
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
        var on = $.post('/advertise/marketplace/activation/', {
            activate: 'true'
        });

        on.error(function() {
            Toast.error("There was an error saving your Marketplace settings. Our support team has been notified. Please refresh your page and try again.");
        });

        on.done(function() { });

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
        var off = $.post('/advertise/marketplace/activation/', {
            activate: 'false'
        });
        $(".targeting-box").attr('disabled', true);
        $("#blindness").attr('disabled', true);
        return true;
    }

    /*
     * Converts a date to a string in the form MM-DD-YYYY
     * e.g. dateToMDYString(new Date()) (assuming today is July 25 2012)
     * will produce "07-25-2012".
     */      
    function dateToMDYString(date) {
        var d = date.getDate();
        var m = date.getMonth()+1;
        var y = date.getFullYear();
        return '' + (m <= 9 ? '0' + m : m) + // MM
        '-' + (d <= 9 ? '0' + d : d) + // DD        
        '-' + y; // YYYY
    }

    /*
     * Makes the Creatives Performance tab's datatable
     */
    function makeCreativePerformanceTable (pub_id, blocklist, start_date, end_date) {

        var origin;
        if (!window.location.origin) {
            origin = window.location.protocol
                + "//" + window.location.host + "/";
            window.location.origin = origin;
        } else {
            origin = window.location.origin;
        }

        // MM-DD-YYYY
        var start_date_str = dateToMDYString(start_date);
        var end_date_str = dateToMDYString(end_date);
        
        var creative_data_url = origin
            + "/advertise/marketplace/creatives/";
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
                        start: start_date_str,
                        end: end_date_str,
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
                    cache: false,
                    error: function(data, textStatus, jqXHR) {
                    }
                } );
            },
            // Callback function that takes table data and renders it
            // as a table row. Called on each row's data right before
            // it's rendered in the table (i.e. when a user clicks
            // 'next'/'prev', or changes the number of displayed rows)
            fnRowCallback: function(nRow, aData, iDisplayIndex) {

                $("td:eq(0)", nRow).html("<iframe "
                                         + "width='320px' "
                                         + "height='50px' "
                                         + "onerror='this.location = \"/images/preview_unavailable.png\";' "
                                         + "src='" + aData[0] + "'>"
                                         + "</iframe>");

                var domain = aData[1];
                if (_.contains(blocklist, domain)) {
                    $("td:eq(1)", nRow).text(domain + " (Blocked)");
                } else if (domain != null) {
                    // Please leave this commented. This feature will be uncommented and used
                    // in the future. Thanks.
                    // var anchor = $("<a href='#'> Block </a>").click(function (event) {
                    //     var $this = $(this);
                    //     event.preventDefault();
                    //     var blocklist_xhr = $.post("/advertise/marketplace/settings/blocklist/", {
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
        list_item.attr("id", "blocked_domain")
        list_item.append(anchor);
        $("#blocked_domains").append(list_item);
    }

    function blocklistRemoveClickHandler (event) {
        event.preventDefault();

        var anchor = $(this);
        var domain = anchor.attr('id');
        $("img", anchor.parent()).removeClass('hidden');
        var blocklist_xhr = $.post("/advertise/marketplace/settings/blocklist/", {
            action: 'remove',
            blocklist: domain
        });

        blocklist_xhr.done(function (response) {
            $("img#" + domain).addClass('hidden');
            anchor.parent().fadeOut();
            if ($("#blocked_domains #blocked_domain:visible").size() === 0) {
                $("#none_currently_blocked").fadeIn();
            }
        });

        blocklist_xhr.error(function (response) {
            $("img#" + domain).addClass('hidden');
            Toast.error("There was an error adding to your blocklist. Please try again.");
        });
    }

    var MarketplaceController = {
        initializeIndex: function (bootstrapping_data) {

            // Fill in the stats data for each of the apps and
            // each of their adunits
            var apps = fetchAppsFromKeys(bootstrapping_data.app_keys);
            _.each(bootstrapping_data.app_keys, function(app_key) {
                fetchAdunitsFromAppKey(app_key, bootstrapping_data.marketplace_active);
            });

            // When the apps are finished loading, we render the chart.
            apps.bind('loaded', function() {
                var chart_view = new CollectionChartView({
                    collection: apps,
                    start_date: bootstrapping_data.start_date,
                    display_values: ['rev', 'imp', 'cpm' ] //TODO include cpm
                });
                chart_view.render();
            });

            var table = makeCreativePerformanceTable(bootstrapping_data.pub_key,
                                                     bootstrapping_data.blocklist,
                                                     bootstrapping_data.start_date,
                                                     bootstrapping_data.end_date);

            /*
             * Click handling for the stats breakdown
             * REFACTOR: move this to a common place because it's everywhere
             */
            $('.stats-breakdown tr').click(function(e) {
                var row = $(this);
                if (!row.hasClass('active')) {
                    var table = row.parents('table');
                    $('tr.active', table).removeClass('active');
                    row.addClass('active');
                }
            });

            /*
             * Blindness settings
             */
            $("#blindness").click(function () {
                var loading_img = $("#blindness-spinner").show();
                var saving = $("#blindness-save-status .saving").show();

                var blindness_xhr = $.post("/advertise/marketplace/settings/blindness/",{
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
                    url: '/advertise/marketplace/settings/blocklist/',
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
                var blocklist_xhr = $.post('/advertise/marketplace/settings/blocklist/', {
                    action: 'add',
                    blocklist: blocklist
                });

                blocklist_xhr.done(function (response) {
                    var domains = response['new'];
                    $.each(domains, function(iter, domain) {
                        addToBlocklist(domain);
                    });
                    $("textarea[name='blocklist']").val('');
                    $("#none_currently_blocked").fadeOut();
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

            function post_categories(filter_level, categories, attributes) {
                var loading_img = $("#filter-spinner").show();
                var saving = $("#filter-save-status .saving").show();

                var result = $.post("/advertise/marketplace/settings/content_filter/", {
                    filter_level: filter_level,
                    categories: categories,
                    attributes: attributes,
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
            }

            $("input.content_level").click(function(){
                var filter_level = $(this).val();
                categories = [];
                attributes = [];

                if(filter_level === 'custom') {
                    $('#categories_div').show();
                    categories = $("#categories").val();
                    attributes = $("#attributes").val();
                } else {
                    $('#categories_div').hide();
                }

                post_categories(filter_level, categories, attributes);
            });

            // initialize chosen multiple select for IAB categories
            $("#categories")
                .chosen({no_results_text: "No results matched"})
                .change(function() {
                    var categories = $(this).val();

                    post_categories('custom', categories, $("#attributes").val());
                });

            // initialize chosen multiple select for IAB categories
            $("#attributes")
                .chosen({no_results_text: "No results matched"})
                .change(function() {
                    var attributes = $(this).val();

                    post_categories('custom', $("#categories").val(), attributes);
                });
        }
    };

    window.MarketplaceController = MarketplaceController;

})(this.jQuery, this._);
