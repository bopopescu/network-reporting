/*
 * # Mopub Marketplace JS
 */
var mopub = mopub || {};
(function($, Backbone) {

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
        validate: function(attributes) {
            var valid_number = Number(attributes.price_floor);
            if (valid_number == NaN) {
                return "please enter a valid number for the price floor";
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
            $(".revenue", app_row).text(this.model.get("revenue"));
            $(".impressions", app_row).text(this.model.get("impressions"));
            $(".ecpm", app_row).text(this.model.get("ecpm"));
            // $(".clicks", app_row).text(this.model.get("clicks"));
            // $(".ctr", app_row).text(this.model.get("ctr"));

            /* Don't load this dynamically for now
            var adunit_show_link = $('a.adunits', app_row);
            adunit_show_link.click(showAdUnits).click();
            $('a.edit_price_floor', app_row).click(function(e) {
                e.preventDefault();
                adunit_show_link.click();
            });
            $('a.view_targeting', app_row).click(function(e) {
                e.preventDefault();
                adunit_show_link.click();
                $(this).addClass('hidden');
            });
            *****/
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

            $(".revenue", adunit_row).text(this.model.get("revenue"));
            $(".ecpm", adunit_row).text(this.model.get("ecpm"));
            $(".impressions", adunit_row).text(this.model.get("impressions"));
            $(".price_floor", adunit_row).html('<input id="' +
                                               this.model.id +
                                               '" type="text" class="input-text input-text-number number" style="width:50px;margin: -3px 0;" value="' +
                                               this.model.get("price_floor") +
                                               '"> USD <img class="loading-img hidden"  src="/images/icons-custom/spinner-12.gif"></img>');
            $(".targeting", adunit_row).html('<input class="targeting-box" type="checkbox"> <img class="loading-img hidden" ' +
                                             ' src="/images/icons-custom/spinner-12.gif"></img>');
            if (this.model.get("active")) {
                $("input.targeting-box", adunit_row).attr('checked', 'checked');
            }

            // Add the event handler to submit targeting changes over ajax.
            $("input.targeting-box", adunit_row).click(function() {
                var loading_img = $(".targeting .loading-img", adunit_row);
                loading_img.show();
                current_model.set({'active': $(this).is(":checked")});
                current_model.save({}, {
                    success: function () {
                        setTimeout(function() {
                            loading_img.hide();
                        }, 2000);
                    }
                });
            });

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor .input-text', adunit_row).keyup(function() {
                var loading_img = $(".price_floor .loading-img", adunit_row);
                loading_img.show();
                current_model.set({'price_floor': $(this).val()});
                current_model.save({}, {
                    success: function () {
                        setTimeout(function() {
                            loading_img.hide();
                        }, 2000);
                    }
                });
            });

            return this;
        },

        // Render the adunit model in the template. This assumes that the table
        // row for the app has already been rendered. This will render underneath it's
        // app's row.
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
         * Fetches all app stats using a list of app keys and renders them into table rows that have already
         * been created in the page. Useful for decreasing page load time along with `fetchAdunitStats`.
         */
        fetchAppStats: function (app_keys) {
            _.each(app_keys, function(app_key) {
                var app = new App({id: app_key});
                app.bind('change', function(current_app) {
                    var appView = new AppView({ model: current_app, el: '#marketplace_stats' });
                    appView.renderInline();
                });
                app.fetch();
            });
        },

        /*
         * Fetches AdUnit stats over ajax and renders them in already existing table rows.
         * This method is useful for decreasing page load time. Uses a parent app's key
         * to bootstrap the fetch.
         */
        fetchAdunitStats: function (app_key) {
          var adunits = new AdUnitCollection();
          adunits.app_id = app_key;

          // Once the adunits have been fetched from the server,
          // render them as well as the app's price floor range
          adunits.bind('reset', function(adunits_collection) {
            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
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
              }
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

                // Disable the 'view' link in the app row under the targeting column
                $(".app-row#app-" + app_key + " .view_targeting").addClass("hidden");

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
            var adunit_classes = adunit.attr('class').split(' ');

            _.each(adunit_classes, function(adunit_class) {

                if (adunit_class.search('for-app-') >= 0) {
                    app_id = adunit_class.replace('for-app-', '');
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
                }
            });
            return true;
        },

        /*
         * Makes the Creatives Performance tab's datatable
         */
        makeCreativePerformanceTable: function (pub_id, dsp_keys, blocklist) {
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
                // Don't resize table columns, we'll do it manually
                bAutoWidth:false,
                // Sort by revenue descending from the start
                aaSorting: [[2,'desc']],
                // Endpoint to fetch table data
                //sAjaxSource: "http://mpx.mopub.com/stats/creatives",
                sAjaxSource: "http://mpx.mopub.com/stats/creatives",
                fnServerData: function( sUrl, aoData, fnCallback ) {
                    $.ajax({
                        url: sUrl,
                        data: {
                            pub_id: pub_id,
                            start: "10-24-2011",
                            end: "10-27-2011",
                            format:'jsonp'
                        },
                        //success: fnCallback,
                        success: function(data, textStatus, jqXHR) {

                            var creative_data = _.map(data, function(creative, key) {
                                var ecpm = (creative['stats']['pub_rev'] / (creative['stats']['imp']+1))*1000;
                                return [
                                    creative["creative"]["url"],
                                    creative["creative"]["ad_dmn"],
                                    creative["stats"]["pub_rev"],
                                    ecpm,
                                    creative["stats"]["imp"]
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
                fnRowCallback: function(nRow, aData, iDisplayIndex) {

                    $("td:eq(0)", nRow).html("<iframe width='320px' height='50px' src='" + aData[0] + "'></iframe>");

                    var domain = aData[1];
                    if (_.contains(blocklist, domain)) {
                        $("td:eq(1)", nRow).text(domain + " (Blocked)");
                     } else if (domain != null) {
                         $("td:eq(1)", nRow).html(domain);
                    } else {
                        $("td:eq(1)", nRow).html("<span class='muted'>(Unknown)</span>");
                    }
                    $("td:eq(2)", nRow).addClass("numeric").text(mopub.Utils.formatCurrency(aData[2]));
                    $("td:eq(3)", nRow).addClass("numeric").text(mopub.Utils.formatCurrency(aData[3]));
                    $("td:eq(4)", nRow).addClass("numeric").text(mopub.Utils.formatNumberWithCommas(aData[4]));
                    return nRow;
                }
            });

            return table;
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
            widgets: ['adunitSorting'],
            sortList: [[1, 0]],
            headers: { 0: { sorter: false}, 6: {sorter: false}, 7: {sorter: false} }
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

        $(".lightswitch").lightswitch(Marketplace.turnOn, Marketplace.turnOff);

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


        $('#blocklist-submit').click(function(e) {
            e.preventDefault();
            $("#addblocklist").submit();
        });

        /*---------------------------------------/
        / Marketplace Graph
        /---------------------------------------*/

        function getCurrentChartSeriesType() {
            var activeBreakdownsElem = $('#dashboard-stats .stats-breakdown .active');
            if (activeBreakdownsElem.attr('id') == 'stats-breakdown-ecpm') return 'line';
            else return 'area';
        }

        // Use breakdown to switch charts
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

        /*---------------------------------------/
        / UI
        /---------------------------------------*/

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
                    document.location.href = location+'?r='+num_days+'&s='+from_year+"-"+from_month+"-"+from_day + hash;
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
          }
          else {
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
            var date = $.datepicker.parseDate(instance.settings.dateFormat || $.datepicker._defaults.dateFormat, selectedDate, instance.settings);
            other.datepicker('option', 'minDate', date);
          }
        });
        $('#dashboard-dateOptions-custom-to').datepicker({
          defaultDate: '-1d',
          maxDate: '0d',
          onSelect: function(selectedDate) {
            var other = $('#dashboard-dateOptions-custom-from');
            var instance = $(this).data("datepicker");
            var date = $.datepicker.parseDate(instance.settings.dateFormat || $.datepicker._defaults.dateFormat, selectedDate, instance.settings);
            other.datepicker('option', 'maxDate', date);
          }
        });
    });


})(this.jQuery, this.Backbone);