/*
 * # MoPub Publisher/Inventory Javascript
 * ## Client-side functionality for the following pages:
 * * Inventory
 * * Dashboard
 * * App detail
 * * Adunit detail
 * * App creation
 * * Sign up flow
 * * Geographical targeting (deprecated)
 */

var mopub = mopub || {};

(function($, Backbone, _){

    var COLOR_THEME = {
            stroke: ['#C8CFD6', '#9EB1C1'],
            color: ['#E5F1FB', '#A3C1DA']
    };


    /*
     * ## Helpers for DashboardController
     */

    var toast_error = function () {
        var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    function format_stat(stat, value) {
        switch (stat) {
          case 'attempts':
          case 'clk':
          case 'conv':
          case 'imp':
          case 'req':
            return number_compact(value, 10);
          case 'cpm':
          case 'rev':
            return '$' + number_compact(value, 10);
          case 'conv_rate':
          case 'ctr':
          case 'fill_rate':
            return mopub.Utils.formatNumberAsPercentage(value);
        default:
            throw new Error('Unsupported stat "' + stat + '".');
        }
    }

    function number_compact(number, multiplier) {
        if (number >= 1000000*multiplier) {
                return mopub.Utils.formatNumberWithCommas(Math.round(number / 1000000)) + 'M';
        }
        if (number >= 1000*multiplier) {
            return mopub.Utils.formatNumberWithCommas(Math.round(number / 1000)) + 'k';
        }
        return mopub.Utils.formatNumberWithCommas(Math.round(number));
    }

    /*
     * Refactor/remove
     */
    function getCurrentChartSeriesType() {
        var activeBreakdownsElem = $('#dashboard-stats .stats-breakdown .active');
        if (activeBreakdownsElem.attr('id') == 'stats-breakdown-ctr') return 'line';
        else return 'area';
    }

    /*
     * Refactor/remove
     */
    function populateGraphWithAccountStats(stats, start_date) {
        var dailyStats = stats["all_stats"]["||"]["daily_stats"];

        mopub.dashboardStatsChartData = {
            pointStart: start_date,
            pointInterval: 86400000,
            requests: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "request_count")}],
            impressions: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "impression_count")}],
            clicks: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "click_count")}],
            users: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "user_count")}]
        };

        mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }

    /*
     * ## fetchAppStats
     * Fetches all app stats using a list of app keys and renders
     * them into table rows that have already been created in the
     * page. Useful for decreasing page load time along with `fetchAdunitStats`.
     */
    function fetchAppStats (app_keys) {
        _.each(app_keys, function(app_key) {
            var app = new App({id: app_key, stats_endpoint: 'all'});
            app.bind('change', function(current_app) {
                var appView = new AppView({ model: current_app, el: '#dashboard-apps' });
                appView.renderInline();
            });
            app.fetch({
                error: function() {
                    app.fetch({
                        error: toast_error
                    });
                }
            });
        });
    }

    /*
     * ## fetchAdunitStats
     * Fetches AdUnit stats for an app over ajax and renders them in already
     * existing table rows. This method is useful for decreasing page load time.
     * Uses a parent app's key to bootstrap the fetch.
     */
    function fetchAdunitStats (app_key) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;
        adunits.stats_endpoint = 'all';
        // Once the adunits have been fetched from the server,
        // render them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {
            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                var adunitView = new AdUnitView({ model: adunit, el: '#dashboard-apps' });
                adunitView.renderInline();
            });
        });

        adunits.fetch({
            success: function(data){
                // Trigger any event handlers that have been attached to the table.
                // Shouldn't this only trigger for the table that the adunit stats are
                // being placed in?
                $('table').trigger('update');
                $("#" + app_key + "-img").hide();
            },
            error: function () {
                adunits.fetch({
                    error: toast_error
                });
            }
        });
    }

    /*
     * ## initializeNewAppForm
     * Loads all click handlers/visual stuff/ajax loading for
     * the app form.
     */
    function initializeNewAppForm() {

        initializeiOSAppSearch();

        $('#appForm-submit')
            .button({
                icons: { secondary: "ui-icon-circle-triangle-e" }
            })
            .click(function(e) {
                e.preventDefault();
                $('#appForm').submit();
            });

        $('#appForm input[name="app_type"]').click(function(e) {
            $('#appForm .appForm-platformDependent')
                .removeClass('iphone')
                .removeClass('android')
                .addClass($(this).val());
        }).filter(':checked').click();

        // Search button
        $('#appForm-search-button')
            .button({ icons: { primary: "ui-icon-search" }})
            .click(function(e) {
                e.preventDefault();
                if ($(this).button( "option", "disabled" )) {
                    return;
                }

                $('#searchAppStore-loading').show();

                $('#dashboard-searchAppStore-custom-modal').dialog({
                    buttons: [
                        {
                            text: 'Cancel',
                            click: function() {
                                $('#searchAppStore-results').html('');
                                $(this).dialog("close");
                            }
                        }
                    ]
                });
                var name = $('#appForm input[name="name"]').val();
                var script = document.createElement("script");
                script.src = 'http://ax.itunes.apple.com'
                    + '/WebObjects/MZStoreServices.woa/wa/wsSearch'+
                    + '?entity=software&limit=10&callback=loadedArtwork&term='
                    + name;
                var head = document.getElementsByTagName("head")[0];
                (head || document.body).appendChild( script );
            });

        if ($('#appForm-name').val() === '') {
            $('#appForm-search-button').button("disable");
            $('#appForm-search').button("disable");
            $('#appForm-market-search-button').button("disable");
            $('#appForm-market-search').button("disable");
        }

        $('#appForm-name').keyup(function(e) {
            // Show/hide the app search button
            var name = $.trim($(this).val());
            var type = $('input:radio[name="app_type"]:checked').val();

            if (name.length) {
                $('#appForm-search-button').button("enable");
                $('#appForm-market-search-button').button('enable');
            } else {
                $('#appForm-search-button').button("disable");
                $('#appForm-market-search-button').button('disable');
            }
            if (e.keyCode == 13) {
                if (type == 'iphone') {
                    $('#appForm-search-button').click();
                } else if (type == 'android') {
                    $('#appForm-market-search-button').click();
                }
            }
        });

        $('#appForm-changeIcon-link').click(function (e) {
            e.preventDefault();
            $(this).hide();
            $('#appForm-icon-upload').show();
            $('#appForm input[name="img_url"]').val('');
        });

        $('input[name="app_type"]').click(function(e) {
            $('#appForm .appForm-platformDependent')
                .removeClass('iphone')
                .removeClass('android')
                .removeClass('mweb')
                .addClass($(this).val());
        }).filter(':checked').click(); // make sure we're in sync when the page Loads
    }

    function initializeEditAppForm() {
        // Set up all of the handlers from the new app form for the new
        // app form.
        initializeNewAppForm();

        // Handler for submitting the edit app form over ajax.
        // If the form submit is successful, the page will reload.
        // If not, the errors will eb displayed.
        $('#appForm.appEditForm').ajaxForm({
            data: { ajax: true },
            dataType: 'json',
            success: function(jsonData, statusText, xhr, $form) {

                // Hide the loading spinner
                $('#appEditForm-loading').hide();

                // Reload the page if the form save was successful
                if (jsonData.success) {
                    window.location.reload();
                } else {
                    // Remove the existing errors before we add the new ones.
                    $('.form-error-text', "#appForm").remove();

                    $.each(jsonData.errors, function (iter, item) {
                        var name = item[0];
                        var error_div = $("<div>").append(item[1]).addClass('form-error-text');

                        $("input[name=" + name + "]", "#appForm")
                            .addClass('error')
                            .parent().append(error_div);

                        $("select[name=" + name + "]", "#appForm")
                            .addClass('error')
                            .parent().append(error_div);
                    });
                    // reimplement the onload event
                    initializeNewAppForm();
                    window.location.hash = '';
                    window.location.hash = 'appForm';
                }
            }
        });

        // When the 'submit' button is clicked, show the loading spinner
        // and submit the form.
        $('#appEditForm-submit')
            .button({
                icons: { secondary: "ui-icon-circle-triangle-e" }
            })
            .click(function(e) {
                e.preventDefault();
                $('#appEditForm-loading').show();
                $('#appForm').submit();
            });

        // When the 'cancel' button is clicked, hide the form by sliding it up
        $('#appEditForm-cancel')
            .click(function(e) {
                e.preventDefault();
                $('#dashboard-appEditForm').slideUp('fast');
            });

        // When the 'edit app settings' button is click, hide/show the app form
        $('#dashboard-apps-editAppButton')
            .button({
                icons: { primary: "ui-icon-wrench" }
            })
            .click(function(e) {
                e.preventDefault();
                if ($('#dashboard-appEditForm').is(':visible')) {
                    $('#dashboard-appEditForm').slideUp('fast');
                } else {
                    $('#dashboard-appEditForm').slideDown('fast');
                }
            });
    }


    /*
     * ## initializeNewAdunitForm
     * Loads all click handlers/visual stuff/ajax loading for
     * the app form.
     */
    function initializeNewAdunitForm() {

        // Set up device format selection UI
        $("#adunit-device_format_phone")
            .parent()
            .buttonset();

        $("#adunit-device_format_phone").click(function(e){
            $('#adForm-tablet-container').hide();
            $('#adForm-phone-container')
                .show()
                .find('input[type="radio"]')[0].click();
        });

        // Click handler for the tablet format
        $('#adunit-device_format_tablet').click(function(e){
            $('#adForm-phone-container').hide();
            $('#adForm-tablet-container')
                .show()
                .find('input[type="radio"]')[0].click();
        });

        // Slide up/down handler for the form div
        $('#dashboard-apps-addAdUnitButton')
            .button({
                icons: { primary: "ui-icon-circle-plus" }
            })
            .click(function(e) {
                e.preventDefault();
                if ($('#dashboard-adunitAddForm').is(':visible'))
                    $('#dashboard-adunitAddForm').slideUp('fast');
                else
                    $('#dashboard-adunitAddForm').slideDown('fast');
            });

        // Submitting over ajax
        $('#adunitAddForm-submit')
            .button({
                icons: { secondary: "ui-icon-circle-triangle-e" }
            })
            .click(function(e) {
                e.preventDefault();
                $('#adunitForm-loading').show();
                $('#adunitAddForm').submit();
            });

        // Cancel button that hides the form
        $('#adunitAddForm-cancel')
            .click(function(e) {
                e.preventDefault();
                $('#dashboard-adunitAddForm').slideUp('fast', function() {
                    $('#dashboard-apps-addAdUnitButton').show();
                });
            });

        $('#adunitAddForm').ajaxForm({
            data: { ajax: true },
            dataType: 'json',
            success: function(jsonData, statusText, xhr, $form) {
                $('#adunitForm-loading').hide();
                if (jsonData.success) {
                    window.location.reload();
                } else {
                    // reimplement the onload event
                    initializeNewAppForm();
                    initializeNewAdunitForm();
                    window.location.hash = '';
                    window.location.hash = 'adunitForm';
                }
            }
        });

        function setDefaultAdUnitName(id) {
            var nameField = $('#appForm-adUnitName');

            // Object that maps id to default ad unit name
            var defaultBannerNames = {
                'appForm-adUnitFormat-banner': 'Banner Ad',
                'appForm-adUnitFormat-tablet-banner': 'Banner Ad',
                'appForm-adUnitFormat-medium': 'Mrect Ad',
                'appForm-adUnitFormat-tablet-medium': 'Mrect Ad',
                'appForm-adUnitFormat-full': 'Fullscreen Ad',
                'appForm-adUnitFormat-full-tablet': 'Fullscreen Ad', // sigh not a typo
                'appForm-adUnitFormat-custom': 'Custom Ad',
                'appForm-adUnitFormat-tablet-custom': 'Custom Ad',
                'appForm-adUnitFormat-tablet-leaderboard': 'Leaderboard Ad',
                'appForm-adUnitFormat-wide-tablet-skyscraper': 'Skyscraper Ad'
            };

            // If the current ad name is a default, we can replace it at will
            $.each(defaultBannerNames, function(key, value) {
                if (nameField.val() === value) {
                    nameField.val(defaultBannerNames[id]);
                    // break out of the loop
                    return false;
                }
            });
        };

        // Set up format selection UI for phone
        $('#adForm-phone-formats').each(function() {
            var container = $(this);

            $('input[type="radio"]', container).click(function(e) {
                var radio = $(this);
                var formatContainer = radio.parents('.adForm-format');
                $('.adForm-format-image').css({ opacity: 0.5 });
                $('.adForm-format-image', formatContainer).css({ opacity: 1 });

                var $full_onlys = $(".full_only");
                var $banner_onlys = $(".banner_only");
                if ($(this).attr("id") == "appForm-adUnitFormat-full-tablet" ||
                    $(this).attr("id") == "appForm-adUnitFormat-full"){
                    $full_onlys.show();
                    $banner_onlys.hide();
                } else {
                    $full_onlys.hide();
                    $banner_onlys.show();
                }

                var $custom_onlys = $(".custom_only");
                if ($(this).attr("id") == "appForm-adUnitFormat-tablet-custom" ||
                    $(this).attr("id") == "appForm-adUnitFormat-custom") {
                    $custom_onlys.show();
                } else {
                    $custom_onlys.hide();
                }

                setDefaultAdUnitName($(this).attr("id"));

            }).filter(':checked').click();

            $('.adForm-format-image', container).click(function(e) {
                var image = $(this);
                var formatContainer = image.parents('.adForm-format');
                $('input[type="radio"]', formatContainer).click();
            });

            $('.adForm-format-details input[type="text"]', container).focus(function() {
                var input = $(this);
                var formatContainer = input.parents('.adForm-format');
                $('input[type="radio"]', formatContainer).click();
            });
        });

        // Set up format selection UI for tablet
        $('#adForm-tablet-formats').each(function(){
            var container = $(this);
            //bind radio buttons to images
            $(this).find('input[type="radio"]').click(function(e) {
                var index = $(this).parent().index();
                var images = $("#adForm-images-container");
                images.children().hide();
                var image = images.children()[index];
                $(image).show().css({ opacity: 1 });

                var $full_onlys = $(".full_only");
                var $banner_onlys = $(".banner_only");
                if ($(this).attr("id") == "appForm-adUnitFormat-full-tablet" ||
                    $(this).attr("id") == "appForm-adUnitFormat-full"){
                    $full_onlys.show();
                    $banner_onlys.hide();
                } else {
                    $full_onlys.hide();
                    $banner_onlys.show();
                }

                var $custom_onlys = $(".custom_only");
                if ($(this).attr("id") == "appForm-adUnitFormat-tablet-custom" ||
                    $(this).attr("id") == "appForm-adUnitFormat-custom"){
                    $custom_onlys.show();
                } else {
                    $custom_onlys.hide();
                }

                setDefaultAdUnitName($(this).attr("id"));

            }).first().click(); //initialize by activating the first
        });

        //initialize checked elements
        $("#adunit-device_format_phone").parent().children()
            .filter(':checked')
            .click()
            .each(function() {
                var deviceFormat = $(this).val(); //either tablet or phone
                var container = "#adForm-" + deviceFormat + "-container";
                $(container).find('.possible-format').click();
            });
        }

    /*
     * ## initializeEditAdunitForm
     * Like the app editing form, the adunit editing form is done
     * over ajax and is displayed in div that slides in and out of
     * the page.
     */
    function initializeEditAdunitForm() {

        initializeNewAdunitForm();

        $('#dashboard-apps-editAdUnitButton')
            .button({ icons: { primary: "ui-icon-wrench" } })
            .click(function(e) {
                e.preventDefault();
                if ($('#dashboard-adunitEditForm').is(':visible'))
                    $('#dashboard-adunitEditForm').slideUp('fast');
                else
                    $('#dashboard-adunitEditForm').slideDown('fast');
            });

        $('#adunitEditForm-submit')
            .button({
                icons: { secondary: "ui-icon-circle-triangle-e" }
            })
            .click(function(e) {
                e.preventDefault();
                $('#adunitForm-loading').show();
                $('#adunitAddForm').submit();
            });

        $('#adunitEditForm-cancel')
            .click(function(e) {
                e.preventDefault();
                $('#dashboard-adunitEditForm').slideUp('fast');
            });

        $('#adunitAddForm').ajaxForm({
            data: {
                ajax: true
            },
            dataType: 'json',
            success: function(jsonData, statusText, xhr, $form) {
                $('#adunitForm-loading').hide();
                if (jsonData.success) {
                    window.location.reload();
                } else {

                    // reimplement the onload event
                    initializeNewAppForm();
                    initializeNewAdunitForm();
                    window.location.hash = '';
                    window.location.hash = 'adunitForm';
                }
            }
        });
    }

    /*
     * ## initializeDailyCounts
     * Initializes click handlers in the daily counts section for the
     * app/adunit detail pages.
     */
    function initializeDailyCounts() {

        var button = $('.appData-details-toggleButton');
        button.button();

        var individual_daily_counts = $("#appData-individual");

        button.click(function(e) {
            e.preventDefault();
            if (individual_daily_counts.hasClass("hidden")) {
                individual_daily_counts.removeClass("hidden");
                button.button('option', 'label', 'Hide Details');
            } else {
                individual_daily_counts.addClass("hidden");
                button.button('option', 'label', 'Show Details');
                button.button();
            }
        });
    }

    /*
     * ## initializeDateButtons
     * Loads all click handlers/visual stuff for the date buttons. Used
     * on a ton of pages, probably could be refactored by someone brave
     * enough.
     */
    function initializeDateButtons () {
        $('#dashboard-dateOptions input').click(function() {
            var option = $(this).val();
            if (option == 'custom') {
                $('#dashboard-dateOptions-custom-modal').dialog({
                    width: 570,
                    buttons: [
                        {
                            text: 'Set dates',
                            css: { fontWeight: '600' },
                            click: function() {
                                var from_date = $('#dashboard-dateOptions-custom-from').datepicker("getDate");
                                var to_date = $('#dashboard-dateOptions-custom-to').datepicker("getDate");
                                var num_days = Math.ceil((to_date.getTime()-from_date.getTime())/(86400000)) + 1;

                                var from_day = from_date.getDate();
                                // FYI, months are indexed from 0
                                var from_month = from_date.getMonth() + 1;
                                var from_year = from_date.getFullYear();

                                $(this).dialog("close");
                                var location = document.location.href.replace(/\?.*/,'');
                                document.location.href = location
                                    + '?r=' + num_days
                                    + '&s=' + from_year + "-" + from_month + "-" + from_day;
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
                var location = document.location.href.replace(/\?.*/,'');
                document.location.href = location + '?r=' + option;
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
                var date = $.datepicker.parseDate(instance.settings.dateFormat
                                                  || $.datepicker._defaults.dateFormat,
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
                var date = $.datepicker.parseDate(instance.settings.dateFormat ||
                                                  $.datepicker._defaults.dateFormat,
                                                  selectedDate,
                                                  instance.settings);
                other.datepicker('option', 'maxDate', date);
            }
        });
    }

    /*
     * ## initializeDeleteForm
     * Deleting apps/adunits is done with a form that's submitted via a dialog.
     * The ajax submitting of the form and the dialog popup are done here.
     */
    function initializeDeleteForm() {
        $('#dashboard-delete-link').click(function(e){
            e.preventDefault();
            $('#dashboard-delete-modal').dialog({
                buttons: [
                    {
                        text: 'Delete',
                        click: function() {
                            $(this).dialog('close');
                            $('#dashboard-deleteForm').submit();
                        }
                    },
                    {
                        text: 'Cancel',
                        click: function() {
                            $(this).dialog('close');
                        }
                    }
                ]
            });
        });
    }

    /*
     * ## initializeiOSAppSearch
     * Sets up the iTunes app store searching functionality for creating new apps.
     */
    function initializeiOSAppSearch() {
        // Search button
        $('#appForm-search-button')
            .button({ icons: { primary: "ui-icon-search" }})
            .click(function(e) {
                e.preventDefault();
                if ($(this).button( "option", "disabled" )) {
                    return;
                }

                $('#searchAppStore-loading').show();

                $('#dashboard-searchAppStore-custom-modal').dialog({
                    buttons: [
                        {
                            text: 'Cancel',
                            click: function() {
                                $('#searchAppStore-results').html('');
                                $(this).dialog("close");
                            }
                        }
                    ]
                });
                var name = $('#appForm input[name="name"]').val();
                var script = document.createElement("script");
                script.src = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch?'
                    + 'entity=software&limit=10&callback=loadedArtwork&term='
                    + name;
                var head = document.getElementsByTagName("head")[0];
                (head || document.body).appendChild( script );
            });
    }

    /*
     * # initializeCommon
     * This function groups together a couple of pieces of functionality that are used on
     * all of the publisher pages (inventory, app, adunit stuff)
     */
    function initializeCommon() {
        initializeDateButtons();
        // Use breakdown to switch charts
        $('.stats-breakdown tr').click(function(e) {
            $('#dashboard-stats-chart').fadeOut(100, function() {
                mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
                $(this).show();
            });
        });

        $('.stats-breakdown tr').click(function(e) {
            var row = $(this);
            if (!row.hasClass('active')) {
                var table = row.parents('table');
                $('tr.active', table).removeClass('active');
                row.addClass('active');
            }
        });

        $('.appData-id').each(function() {
            var id = $(this);
            var td = id.parents('tr');
            td.hover(
                function() {
                    id.show();
                },
                function() {
                    id.hide();
                });
        });
    }

    function createChart(series, element, account_data, options) {

        console.log(account_data);

        var all_chart_data = _.map(account_data, function(range, i){
            var individual_series_data = {
                data: _.map(range, function(datapoint, j){

                    var timeslice;
                    if (datapoint.hasOwnProperty('hour')) {
                        timeslice = new Date('date');
                    } else if (datapoint.hasOwnProperty('date')) {
                        timeslice = new Date('date');
                    } else {
                        timeslice = j;
                    }

                    return { 
                        x: j, 
                        y: datapoint[series] 
                    };
                }),
                stroke: COLOR_THEME.stroke[i],
                color: COLOR_THEME.color[i]
            };            
            return individual_series_data;
        });

        // Hack to clear any current charts from the element. Rickshaw
        // doesn't remove the old chart from the element before it
        // renders a new one, so we have to do it manually.
        $(element).html('');

        // Create the new chart with our series data
        var chart = new Rickshaw.Graph({
            element: document.querySelector(element), 
            width: 550, 
            height: 150, 
            renderer: 'area',
            stroke: true,
            series: all_chart_data
        });

        var hoverDetail = new Rickshaw.Graph.HoverDetail( {
            graph: chart,
            width: 550, 
            height: 150, 
            xFormatter: function(x) { return x; },
            yFormatter: function(y) { return format_stat(series, y); }
        });

        var xAxis = new Rickshaw.Graph.Axis.Time({
	        graph: chart,
	        ticksTreatment: 'glow',
        });
        xAxis.render();
        
        var yAxis = new Rickshaw.Graph.Axis.Y({ 
	        graph: chart,
	        tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
	        ticksTreatment: 'glow'
        } );
        yAxis.render();


        chart.renderer.unstack = true;
        chart.render();
        return chart;
    }

    function initializeDashboardCharts(start_date, end_date, account_data) {
        var rev_chart = createChart('rev', '#rev_chart', account_data);
        var imp_chart = createChart('imp', '#imp_chart', account_data);
        var clk_chart = createChart('clk', '#clk_chart', account_data);
        var ctr_chart = createChart('ctr', '#ctr_chart', account_data);
    }

    /*
     * ## Dashboard Controller
     */
    var DashboardController = {
        initializeIndex: function (bootstrapping_data) {

            // Adds click handlers for the top date buttons and stats breakdown
            // date buttons, and click handlers for the stats breakdown graph-
            // changing
            initializeCommon();

            // Populate the graph
            populateGraphWithAccountStats(bootstrapping_data.account_stats,
                                          bootstrapping_data.start_date);

            // Populate the app/adunit stats table
            fetchAppStats(bootstrapping_data.app_keys);
            _.each(bootstrapping_data.app_keys, function(app_key) {
                fetchAdunitStats(app_key);
            });

            // Add icon to the 'Add an app' button
            // Remove later with new button treatment
            $('#dashboard-apps-addAppButton')
                .button({ icons: { primary: "ui-icon-circle-plus" } });

            // Do Dashboard export
            $('#publisher-dashboard-exportSelect')
                .change(function(e) {
                    e.preventDefault();
                    var val = $(this).val();
                    if (val != 'exp') {
                        $('#dashboardExportForm')
                .find('#appExportType')
                            .val(val)
                            .end()
                            .submit();
                    }
                    $(this).selectmenu('index', 0);
                });


            // Hide unneeded li entry
            $('#publisher-dashboard-exportSelect-menu').find('li').first().hide();
        },

        initializeDashboard: function(bootstrapping_data) {
            /**
             * TODO: document
             *
             * bootstrapping_data: {
             *     account: account key,
             *     names: {
                       key: name
             *     }
             * }
             */

            /* Constants */
            var URL = 'http://ec2-23-22-32-218.compute-1.amazonaws.com/';
            var URL = 'http://localhost:8888/';

            var STATS = {
                'attempts': 'Attempts',
                'clk': 'Clicks',
                'conv': 'Conversions',
                'conv_rate': 'Conversion Rate',
                'cpm': 'CPM',
                'ctr': 'CTR',
                'fill_rate': 'Fill Rate',
                'imp': 'Impressions',
                'req': 'Requests',
                'rev': 'Revenue'
            };

            var WIDTH = 550;
            var HEIGHT = 150;

            var MARGIN_TOP = 10;
            var MARGIN_RIGHT = 30;
            var MARGIN_BOTTOM = 15;
            var MARGIN_LEFT = 50;

            function calculate_stats(obj) {
                obj.conv_rate = obj.imp === 0 ? 0 : obj.conv / obj.imp;
                obj.cpm = obj.imp === 0 ? 0 : 1000 * obj.clk / obj.imp;
                obj.ctr = obj.imp === 0 ? 0 : obj.clk / obj.imp;
                obj.fill_rate = obj.req === 0 ? 0 : obj.imp / obj.req;
            }

            /* JSONP Setup */
            $.jsonp.setup({
                callbackParameter: "callback",
                dataFilter: function (json) {
                    _.each(['sum', 'vs_sum'], function (key) {
                        _.each(json[key], function (obj) {
                            calculate_stats(obj);
                        });
                    });
                    _.each(['daily', 'hourly', 'vs_daily', 'vs_hourly', 'top', 'vs_top'], function (key) {
                        _.each(json[key], function (list) {
                            _.each(list, function (obj) {
                                calculate_stats(obj);
                            });
                        });
                    });
                    return json;
                },
                error: toast_error,
                url: URL
            });

            /* TODO: use routers
            var Dashboard = Backbone.Router.extend({

                routes: {
                    ":start_date/:end_date/": "update"   // #search/kiwis/p7
                },

                update: function(start, end) {
                     var account = bootstrapping_data['account'];
                     var granularity = 'daily';

                     var campaigns = '';

                     var queries = [

                     ];

                     var data = {
                        account: account,
                        start: start,
                        end: end,
                        granularity: granularity,
                        queries: [{
                            campaign: '*', // or just dont include it
                            adgroup: '123',
                            app: '12345',
                            adunit: 'aaa',
                            source: 'direct', // or mpx or networks
                            source_type: 'promo'
                        },{
                            // example: will fetch all promo stats
                            source: 'direct',
                            source_type: 'promo'
                        },{
                            // example: will get all stats for this adunit that
                            // were delivered in this adgroup
                            adgroup: 'asdASidnasdianlsdASD',
                            adunit: 'aaaBBBcccDDDeeeeFFF'
                        }]
                     };

                    $.jsonp({
                        data: data,
                        error: function (xOptions, textStatus) {
                            console.log('JSONP Error: using random data instead.');
                            start_date = string_to_date(start);
                            end_date = string_to_date(end);
                            var date_range = (end_date - start_date) / 86400000 + 1;
                            var series1 = [];
                            var series2 = [];
                            for(var i = 0; i <= date_range; i++) {
                                series1[i] = Math.random() * 200;
                                series2[i] = Math.random() * 200;
                            }
                            var data = {
                                'Series 1': series1,
                                'Series 2': series2
                            };
                            update_chart(start_date, end_date, data);
                        },
                        success: function (json, textStatus) {
                            console.log('Success : ' + json + '.');
                        },
                        url: 'http://statservice.mopub.com/'
                    });
                }

            });

            var dashboard = new Dashboard();

            Backbone.history.start({
                pushState: true,
                root: '/inventory/dashboard/'
            });

            var start_date = new Date(end_date - date_range * 86400000);
            var url = date_to_string(start_date) + '/' + date_to_string(end_date) + '/';
            dashboard.navigate(url, {trigger: true});
            */

            /* Helpers */
            function format_stat(stat, value) {
                switch (stat) {
                    case 'attempts':
                    case 'clk':
                    case 'conv':
                    case 'imp':
                    case 'req':
                        return number_compact(value, 10);
                    case 'cpm':
                    case 'rev':
                        return '$' + number_compact(value, 10);
                    case 'conv_rate':
                    case 'ctr':
                    case 'fill_rate':
                        return mopub.Utils.formatNumberAsPercentage(value);
                    default:
                        throw new Error('Unsupported stat "' + stat + '".');
                }
            }

            function number_compact(number, multiplier) {
                if(number >= 1000000*multiplier) {
                    return mopub.Utils.formatNumberWithCommas(Math.round(number / 1000000)) + 'M';
                }
                if(number >= 1000*multiplier) {
                    return mopub.Utils.formatNumberWithCommas(Math.round(number / 1000)) + 'k';
                }
                return mopub.Utils.formatNumberWithCommas(Math.round(number));
            }

            function string_to_date(date_string) {
                var parts = date_string.split('-');
                return new Date(parts[0], parts[1] - 1, parts[2]);
            }

            function date_to_string(date) {
                return date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate() + '-' + date.getHours();
            }

            function get_charts() {
                return ['rev', 'imp', 'clk', 'ctr'];
            }

            function get_columns() {
                return ['rev', 'imp', 'clk', 'ctr'];
            }

            function get_order() {
                return 'rev';
            }

            function get_keys(type) {
                return _.map($('tr.' + type + ' input:checked'), function (input) {
                    return $(input).closest('tr').attr('id');
                });
            }

            function get_advertiser_type() {
                if($('tr.source input:checked').length) {
                    return 'source';
                }
                if($('tr.campaign input:checked').length) {
                    return 'campaign';
                }
                if($('tr.adgroup input:checked').length) {
                    return 'adgroup';
                }
                return null;
            }

            function get_publisher_type() {
                if($('tr.app input:checked').length) {
                    return 'app';
                }
                if($('tr.adunit input:checked').length) {
                    return 'adunit';
                }
                return null;
            }

            function get_advertiser_query(advertiser) {
                var query = {};
                if(advertiser) {
                    query[advertiser] = get_keys(advertiser);
                }
                return query;
            }

            function get_publisher_query(publisher) {
                var query = {};
                if(publisher) {
                    query[publisher] = get_keys(publisher);
                }
                return query;
            }

            /* Templates */
            var filter_row = _.template($('#filter_row').html());
            var names = bootstrapping_data.names;

            function render_filter_row(data, columns) {
                var context = {
                    type: data.type,
                    id: data.id,
                    selected: data.selected,
                    name: names[data.id],
                    columns: columns,
                    stats: {}
                };

                _.each(columns, function (stat) {
                    context.stats[stat] = format_stat(stat, data.stats[stat]);
                });

                if('vs_stats' in data) {
                    context.stats_delta = {};
                    context.stats_delta_class = {};
                    _.each(columns, function (stat) {
                        if(data.vs_stats[stat] === 0) {
                            context.stats_delta[stat] = '';
                            context.stats_delta_class[stat] = '';
                        }
                        else {
                            var delta = Math.round(100 * (data.stats[stat] - data.vs_stats[stat]) / data.vs_stats[stat]);
                            if(delta === 0) {
                                context.stats_delta[stat] = '~0%';
                                context.stats_delta_class[stat] = '';
                            }
                            else if(delta < 0) {
                                context.stats_delta[stat] = delta + '%';
                                context.stats_delta_class[stat] = 'negative';
                            }
                            else {
                                context.stats_delta[stat] = '+' + delta + '%';
                                context.stats_delta_class[stat] = 'positive';
                            }
                        }
                    });
                }

                return filter_row(context);
            }

            function update_dashboard(update_rollups_and_charts, advertiser_table, publisher_table) {
                var start, end;
                if($('select[name="date_range"]').val() == 'custom') {
                    start = new Date($("#datepicker-start-input").val());
                    end = new Date($("#datepicker-end-input").val());
                }
                else {
                    end = new Date(new Date().toDateString());
                    switch($('select[name="date_range"]').val()) {
                        case 'day':
                            start = end;
                            break;
                        case 'week':
                            start = new Date(end - 86400000 * 6);
                            break;
                        case 'two_weeks':
                            start = new Date(end - 86400000 * 13);
                            break;
                    }
                }
                end.setHours(23);

                var data = {
                    account: bootstrapping_data['account'],
                    start: date_to_string(start),
                    end: date_to_string(end)
                };

                if($('[name="compare"]').is(':checked')) {
                    var diff;
                    switch($('select[name="date_range"]').val()) {
                        case 'day':
                            diff = 86400000;
                            break;
                        case 'week':
                            diff = 86400000 * 7;
                            break;
                        case 'two_weeks':
                            diff = 86400000 * 14;
                            break;
                    }
                    data['vs_start'] = date_to_string(new Date(start - diff));
                    data['vs_end'] = date_to_string(new Date(end - diff));
                }

                var advertiser_type = get_advertiser_type();
                var advertiser_query = get_advertiser_query(advertiser_type);
                var publisher_type = get_publisher_type();
                var publisher_query = get_publisher_query(publisher_type);

                if(update_rollups_and_charts) {

                    var rollups_and_charts_data = _.clone(data);
                    var granularity = $('select[name="granularity"]').val();
                    rollups_and_charts_data.granularity = granularity;
                    rollups_and_charts_data.query = [_.extend(advertiser_query, publisher_query)];

                    if($('[name="advertiser_compare"]').is(':checked')) {

                        _.each(advertiser_query[advertiser_type], function(advertiser) {
                            var query = _.clone(publisher_query);
                            query[advertiser_type] = [advertiser];
                            rollups_and_charts_data.query.push(query);
                        });

                        $.jsonp({
                            data: {
                                data: JSON.stringify(rollups_and_charts_data)
                            },
                            success: function (json, textStatus) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    update_rollups(json.sum[0]);
                                    var charts_data = json[granularity].slice(1);
                                    //update_charts(start, end, charts_data);
                                    initializeDashboardCharts(start, end, charts_data);
                                });
                            }
                        });

                    } else if ($('[name="publisher_compare"]').is(':checked')) {

                        _.each(publisher_query[publisher_type], function(publisher) {
                            var query = _.clone(advertiser_query);
                            query[publisher_type] = [publisher];
                            rollups_and_charts_data.query.push(query);
                        });

                        $.jsonp({
                            data: {
                                data: JSON.stringify(rollups_and_charts_data)
                            },
                            success: function (json, textStatus) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    update_rollups(json.sum[0]);
                                    var charts_data = json[granularity].slice(1);
                                    //update_charts(start, end, charts_data);
                                    initializeDashboardCharts(start, end, charts_data);
                                });
                            }
                        });

                    } else {
                        $.jsonp({
                            data: {
                                data: JSON.stringify(rollups_and_charts_data)
                            },
                            success: function (json, textStatus) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    if(json.vs_sum.length) {
                                        update_rollups(json.sum[0], json.vs_sum[0]);

                                        var charts_data = [
                                            _.extend(json[granularity][0], { name: 'This Period' }),
                                            _.extend(json['vs_' + granularity][0], { name: 'Comparison Period' })
                                        ];

                                        //update_charts(start, end, chart_data);
                                        initializeDashboardCharts(start, end, charts_data);
                                        
                                    } else {
                                        update_rollups(json.sum[0]);
                                        var charts_data = [json[granularity][0]];

                                        //update_charts(start, end, chart_data);
                                        initializeDashboardCharts(start, end, charts_data);
                                    }
                                });
                            }
                        });
                    }
                }

                var order = get_order();
                var columns = get_columns();

                if (advertiser_table) {
                    update_advertiser_table(data, publisher_query, order, columns);
                }

                if (publisher_table) {
                    update_publisher_table(data, advertiser_query, order, columns);
                }
            }

            function update_rollups(data, vs_data) {
                _.each(get_charts(), function (stat) {

                    var rollup = $('#' + stat + ' > div');
                    rollup.children('div.value').html(format_stat(stat, data[stat]));

                    if (vs_data && vs_data[stat] !== 0) {
                        var delta = rollup.children('div.delta');
                        var val = Math.round(100 * (data[stat] - vs_data[stat]) / vs_data[stat]);
                        var html = '';
                        if (val > 0) {
                            html += '+';
                            delta.removeClass('negative');
                            delta.addClass('positive');
                        } else if (val < 0) {
                            delta.removeClass('positive');
                            delta.addClass('negative');
                        } else {
                            html += '~';
                            delta.removeClass('positive');
                            delta.removeClass('negative');
                        }
                        html += val + '%';
                        delta.html(html);
                    } else {
                        rollup.children('div.delta').html('');
                    }
                });
            }

            function update_charts(start, end, data) {
                _.each(get_charts(), function (stat) {
                    // chart
                    var chart = d3.select('#' + stat + ' svg g');
                    chart.selectAll('*').remove();

                    var min;
                    var max;
                    var serieses = _.map(data, function (datum) {
                        return _.map(datum, function (slice) {
                            var value = slice[stat];
                            if(!min || value < min) min = value;
                            if(!max || value > max) max = value;
                            return value;
                        });
                    });

                    /* TODO: reimplement this
                    if(granularity == 'daily') {
                        end = new Date(end.getFullYear(), end.getMonth(), end.getDate());
                    }
                    */

                    if(max == min) {
                        max = min + 1;
                    }
                    var y = d3.scale.linear().domain([min, max]).range([MARGIN_BOTTOM, HEIGHT - MARGIN_TOP]);
                    var x = d3.scale.linear().domain([start, end]).range([MARGIN_LEFT, WIDTH - MARGIN_RIGHT]);

                    // Lines
                    var line = d3.svg.line()
                        .x(function(d, i) { return x(start.getTime()+(end-start)*i/(serieses[0].length - 1)); })
                        .y(function(d) { return -1 * y(d); });

                    _.each(serieses, function (series) {
                        chart.append("svg:path").attr("d", line(series));
                    });

                    // X Axis
                    var x_label = function (d) {
                        d = new Date(d);
                        return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();
                    };
                    var interval = 86400000;
                    /* TODO: reimplement this
                    if(granularity == 'hourly' && end - start <= 2 * 86400000) {
                        x_label = function (d) {
                            return date_to_string(new Date(d));
                        };
                        interval = 3600000;
                    }
                    else {
                    }
                    */

                    if(Math.round((end - start) / (interval * 5)) > 0) {
                        interval = interval * Math.round((end - start) / (interval * 5));
                    }

                    var x_ticks = [];
                    for(var value = start; value <= end; value = new Date(value.getTime() + interval)) {
                        x_ticks.push(value);
                    }

                    chart.append("svg:line")
                        .attr("x1", x(start))
                        .attr("y1", -1 * y(min))
                        .attr("x2", x(end))
                        .attr("y2", -1 * y(min));

                    chart.selectAll(".xLabel")
                        .data(x_ticks)
                        .enter().append("svg:text")
                        .attr("class", "xLabel")
                        .text(x_label)
                        .attr("x", function(d) { return x(d); })
                        .attr("y", 0)
                        .attr("text-anchor", "middle");

                    chart.selectAll(".xTicks")
                        .data(x_ticks)
                        .enter().append("svg:line")
                        .attr("class", "xTicks")
                        .attr("x1", function(d) { return x(d); })
                        .attr("y1", -1 * y(min))
                        .attr("x2", function(d) { return x(d); })
                        .attr("y2", -1 * (y(min) - 4));

                    // Y AXIS
                    chart.append("svg:line")
                        .attr("x1", x(start))
                        .attr("y1", -1 * y(min))
                        .attr("x2", x(start))
                        .attr("y2", -1 * y(max));

                    chart.selectAll(".yTicks")
                        .data(y.ticks(4))
                        .enter().append("svg:line")
                        .attr("class", "yTicks")
                        .attr("y1", function(d) { return -1 * y(d); })
                        .attr("x1", x(start) - 4)
                        .attr("y2", function(d) { return -1 * y(d); })
                        .attr("x2", x(start));

                    chart.selectAll(".yLabel")
                        .data(y.ticks(4))
                        .enter().append("svg:text")
                        .attr("class", "yLabel")
                        .text(function(d) { return number_compact(d, 1); })
                        .attr("x", MARGIN_LEFT - 5)
                        .attr("y", function(d) { return -1 * y(d); })
                        .attr("text-anchor", "end")
                        .attr("dy", 4);
                });
            }

            /* Tables */
            function update_advertiser_table(data, publisher_query, order, columns) {
                selected = _.map($('tr.selected'), function (tr) { return tr.id; });

                $('tr.campaign, tr.adgroup', 'table#advertiser').remove();

                var source_data = _.clone(data);
                source_data.query = [];
                $('tr.source', 'table#advertiser').each(function (index, tr) {
                    var query = _.clone(publisher_query);
                    query.source = [tr.id];
                    source_data.query.push(query);
                });

                $.jsonp({
                    data: {
                        data: JSON.stringify(source_data)
                    },
                    success: function (json) {
                        // defer so exceptions show up in the console
                        _.defer(function() {
                            var sources = [];
                            _.each(source_data.query, function(query, index) {
                                var source = {
                                    type: 'source',
                                    id: query.source[0],
                                    selected: _.include(selected, query.source[0]),
                                    stats: json.sum[index]
                                };
                                if(json.vs_sum.length) {
                                    source.vs_stats = json.vs_sum[index];
                                }
                                sources.push(source);
                            });
                            update_sources(data, publisher_query, order, columns, selected, sources);
                        });
                    }
                });
            }

            function update_sources(data, publisher_query, order, columns, selected, sources) {
                _.each(sources, function (source, source_id) {
                    var $source = $(render_filter_row(source, columns));
                    $('table#advertiser tr#' + source.id).replaceWith($source);
                    if(source_id == 'direct' || source_id == 'network') {
                        var campaign_data = _.clone(data);
                        campaign_data.granularity = 'top';
                        campaign_data.query = [_.extend(_.clone(publisher_query), {
                            source: [source.id],
                            order: order,
                            top: 'campaign'
                        })];

                        $.jsonp({
                            data: {
                                data: JSON.stringify(campaign_data)
                            },
                            success: function(json) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    var campaigns = [];
                                    _.each(json.top[0], function(top, index) {
                                        var campaign = {
                                            type: 'campaign',
                                            id: top.campaign,
                                            selected: _.include(selected, top.campaign),
                                            stats: top
                                        };
                                        if(json.vs_top.length) {
                                            campaign.vs_stats = json.vs_top[0][index];
                                        }
                                        campaigns.push(campaign);
                                    });
                                    update_campaigns(columns, selected, $source, campaigns);
                                });
                            },
                            url: URL + 'topN/'
                        });
                    }
                });
            }

            function update_campaigns(columns, selected, $source, campaigns) {
                var $last = $source;
                _.each(campaigns, function (campaign) {
                    var $campaign = $(render_filter_row(campaign, columns));
                    $last.after($campaign);
                    $last = $campaign;
                });

                // hide unselected rows' stats
                if($('tbody tr.selected', 'table#advertiser').length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', 'table#advertiser').show();
                }
                else {
                    $('tbody tr', 'table#advertiser').each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }
            }

            function update_publisher_table(data, advertiser_query, order, columns) {
                selected = _.map($('tr.selected'), function (tr) { return tr.id; });

                $('tr.app, tr.adunit', 'table#publisher').remove();

                var app_data = _.clone(data);
                app_data.granularity = 'top';
                app_data.query = [_.extend(_.clone(advertiser_query), {
                    order: order,
                    top: 'app'
                })];

                $.jsonp({
                    data: {
                        data: JSON.stringify(app_data)
                    },
                    success: function(json) {
                        // defer so exceptions show up in the console
                        _.defer(function() {
                            var apps = [];
                            _.each(json.top[0], function(top, index) {
                                var app = {
                                    type: 'app',
                                    id: top.app,
                                    selected: _.include(selected, top.app),
                                    stats: top
                                };
                                if(json.vs_top.length) {
                                    app.vs_stats = json.vs_top[0][index];
                                }
                                apps.push(app);
                            });
                            update_apps(data, advertiser_query, order, columns, selected, apps);
                        });
                    },
                    url: URL + 'topN/'
                });
            }

            function update_apps(data, advertiser_query, order, columns, selected, apps) {
                $publisher_table = $('table#publisher tbody');
                _.each(apps, function (app) {
                    var $app = $(render_filter_row(app, columns));
                    $publisher_table.append($app);

                    var adunit_data = _.clone(data);
                    adunit_data.granularity = 'top';
                    adunit_data.query = [_.extend(_.clone(advertiser_query), {
                        app: [app.id],
                        order: order,
                        top: 'adunit'
                    })];

                    $.jsonp({
                        data: {
                            data: JSON.stringify(adunit_data)
                        },
                        success: function (json) {
                            // defer so exceptions show up in the console
                            _.defer(function() {
                                var adunits = [];
                                _.each(json.top[0], function(top, index) {
                                    var adunit = {
                                        type: 'adunit',
                                        id: top.adunit,
                                        selected: _.include(selected, top.adunit),
                                        stats: top
                                    };
                                    if(json.vs_top.length) {
                                        adunit.vs_stats = json.vs_top[0][index];
                                    }
                                    adunits.push(adunit);
                                });
                                update_adunits(columns, selected, $app, adunits);
                            });
                        },
                        url: URL + 'topN/'
                    });
                });
            }

            function update_adunits(columns, selected, $app, adunits) {
                var $last = $app;
                _.each(adunits, function (adunit) {
                    var $adunit = $(render_filter_row(adunit, columns));
                    $last.after($adunit);
                    $last = $adunit;
                });

                // hide unselected rows' stats
                if($('tbody tr.selected', 'table#publisher').length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', 'table#publisher').show();
                }
                else {
                    $('tbody tr', 'table#publisher').each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }
            }

            /* Controls */
            // date controls
            // Set up the two date fields with datepickers
            var valid_date_range = {
                endDate: "0d"
            };
            $("input[name='start-date']").datepicker(valid_date_range);
            $("input[name='end-date']").datepicker(valid_date_range);

            // On submit, get the date range from the two inputs and
            // form the url, and reload the page.
            $("#custom-date-submit").unbind('click').click(function() {
                $('#custom_date_range').html($("#datepicker-start-input").val() + ' to ' + $("#datepicker-end-input").val());
                $('#custom_date_range').show();
                $("#datepicker-custom-range").toggleClass('hidden');
                update_dashboard(true, true, true);
            });

            $("#custom_date_range").click(function () {
                $("#datepicker-custom-range").toggleClass('hidden');
            });

            $('[name="date_range"]').change(function () {
                if($(this).val() == 'custom') {
                    $("#datepicker-custom-range").toggleClass('hidden');
                    $('[name="compare"]').removeProp('checked');
                    $('[name="compare"]').closest('label').hide();
                }
                else {
                    $('#custom_date_range').hide();
                    $('[name="compare"]').closest('label').show();
                    if($(this).val() == 'day') {
                        // granularity can't be daily
                        if($('[name="granularity"]').val() == 'daily') {
                            $('[name="granularity"]').val('hourly');
                        }
                        $('[name="granularity"] option[value="daily"]').attr('disabled', 'disabled');
                        $('span#comparison_range').html('yesterday');
                    }
                    else {
                        // granularity can be daily
                        $('[name="granularity"] option[value="daily"]').removeAttr('disabled');
                        if($(this).val() == 'week') {
                            $('span#comparison_range').html('the week before');
                        }
                        else if($(this).val() == 'two_weeks') {
                            $('span#comparison_range').html('the two weeks before');
                        }
                    }
                    update_dashboard(true, true, true);
                }
            });

            // granularity
            $('[name="granularity"]').change(function () {
                update_dashboard(true, false, false);
            });

            // comparison
            $('[name="compare"]').change(function () {
                $('[name="advertiser_compare"]').prop('checked', false);
                $('[name="publisher_compare"]').prop('checked', false);
                update_dashboard(true, true, true);
            });
            $('[name="advertiser_compare"]').change(function () {
                $('[name="compare"]').prop('checked', false);
                $('[name="publisher_compare"]').prop('checked', false);
                update_dashboard(true, true, true);
            });
            $('[name="publisher_compare"]').change(function () {
                $('[name="compare"]').prop('checked', false);
                $('[name="advertiser_compare"]').prop('checked', false);
                update_dashboard(true, true, true);
            });

            // export
            $('button#export').click(function () {
                var advertiser_type = get_advertiser_type();
                $('#export_wizard select[name="advertiser_breakdown"]')
                    .children('option')
                    .each(function (index, option) {
                        $(option).prop('disabled', ($(option).val() !== '' && $(option).val() !== advertiser_type));
                });
                
                var publisher_type = get_publisher_type();
                $('#export_wizard select[name="publisher_breakdown"]').children('option').each(function (index, option) {
                    $(option).prop('disabled', ($(option).val() !== '' && $(option).val() !== publisher_type));
                });
                $('#export_wizard').modal('show');
            });

            $('button#download').click(function () {

                // Hide the modal when the download button is clicked. 
                $('#export_wizard').modal('hide');


                // Extrapolate the start and end date
                var start, end;
                if ($('select[name="date_range"]').val() == 'custom') {
                    start = new Date($("#datepicker-start-input").val());
                    end = new Date($("#datepicker-end-input").val());
                } else {
                    end = new Date(new Date().toDateString());
                    switch($('select[name="date_range"]').val()) {
                        case 'day':
                            start = end;
                            break;
                        case 'week':
                            start = new Date(end - 86400000 * 6);
                            break;
                        case 'two_weeks':
                            start = new Date(end - 86400000 * 13);
                            break;
                        default: start = end;                        
                    }
                }

                end.setHours(23);

                // Determine the query
                var query = {};

                var advertiser_breakdown = $('select[name="advertiser_breakdown"]').val();
                query[advertiser_breakdown] = get_keys(advertiser_breakdown);
                var publisher_breakdown = $('select[name="publisher_breakdown"]').val();
                query[publisher_breakdown] = get_keys(publisher_breakdown);

                // REFACTOR: this can be removed once we have real data in the tables
                // Map id's to names so that we can include them in the table
                var names = {};
                _.each(query[advertiser_breakdown], function(id) {
                    names[id] = $.trim($('#' + id + ' td.name').html());
                });
                _.each(query[publisher_breakdown], function(id) {
                    names[id] = $.trim($('#' + id + ' td.name').html());
                });

                var data = {
                    account: bootstrapping_data['account'],
                    start: date_to_string(start),
                    end: date_to_string(end),
                    granularity: $('select[name="granularity"]').val(),
                    advertiser_breakdown: advertiser_breakdown,
                    publisher_breakdown: publisher_breakdown,
                    query: query,
                    names: names
                };

                window.location = URL + 'csv/?data=' + JSON.stringify(data);

            });

            /* Advertiser Table */
            var advertiser_table = $('table#advertiser');

            // select sources
            $('tbody tr.source', advertiser_table).live('click', function () {
                $(this).toggleClass('selected');

                // select or deselect this source's campaigns
                if($(this).hasClass('selected')) {
                    $(this).nextUntil('.source').addClass('selected');
                }
                else{
                    $(this).nextUntil('.source').removeClass('selected');
                }

                // hide unselected rows' stats
                if($('tbody tr.selected', advertiser_table).length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', advertiser_table).show();
                }
                else {
                    $('tbody tr', advertiser_table).each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }

                update_dashboard(true, false, true);
            });

            // select campaigns
            $('tbody tr.campaign', advertiser_table).live('click', function () {
                $(this).toggleClass('selected');

                // TODO: there has to be a better way to select this...
                $source = $(this).prev();
                while(!$source.hasClass('source')) {
                    $source = $source.prev();
                }
                if($(this).hasClass('selected')) {
                    var selected = true;
                    $source.nextUntil('.source').each(function () {
                        if(!$(this).hasClass('selected')) {
                            selected = false;
                        }
                    });
                    if(selected) {
                        $source.addClass('selected');
                    }
                    else {
                        $source.removeClass('selected');
                    }
                }
                else {
                    $source.removeClass('selected');
                }

                // hide unselected rows' stats
                if($('tbody tr.selected', advertiser_table).length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', advertiser_table).show();
                }
                else {
                    $('tbody tr', advertiser_table).each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }

                update_dashboard(true, false, true);
            });

            /*
            // expand adgroups
            $('tr.campaign button.expand', advertiser_table).live('click', function () {
                $(this).closest('tr').nextUntil('tr.campaign').show();
                $(this).removeClass('expand');
                $(this).addClass('collapse');
            });

            // collapse adgroups
            $('tr.campaign button.collapse', advertiser_table).live('click', function () {
                $(this).closest('tr').nextUntil('tr.campaign').hide();
                $(this).removeClass('collapse');
                $(this).addClass('expand');
            });
            */

            /* Publisher Table */
            var publisher_table = $('table#publisher');

            // select apps
            $('tbody tr.app', publisher_table).live('click', function () {
                $(this).toggleClass('selected');

                // select or deselect this source's campaigns
                if($(this).hasClass('selected')) {
                    $(this).nextUntil('.app').addClass('selected');
                }
                else{
                    $(this).nextUntil('.app').removeClass('selected');
                }

                // hide unselected rows' stats
                if($('tbody tr.selected', publisher_table).length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', publisher_table).show();
                }
                else {
                    $('tbody tr', publisher_table).each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }

                update_dashboard(true, true, false);
            });

            // select adunits
            $('tbody tr.adunit', publisher_table).live('click', function () {
                $(this).toggleClass('selected');

                // TODO: there has to be a better way to select this...
                $app = $(this).prev();
                while(!$app.hasClass('app')) {
                    $app = $app.prev();
                }
                if($(this).hasClass('selected')) {
                    var selected = true;
                    $app.nextUntil('.app').each(function () {
                        if(!$(this).hasClass('selected')) {
                            selected = false;
                        }
                    });
                    if(selected) {
                        $app.addClass('selected');
                    }
                    else {
                        $app.removeClass('selected');
                    }
                }
                else {
                    $app.removeClass('selected');
                }

                // hide unselected rows' stats
                if($('tbody tr.selected', publisher_table).length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', publisher_table).show();
                }
                else {
                    $('tbody tr', publisher_table).each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }

                update_dashboard(true, true, false);
            });

            /*
            // expand adunits
            $('tr.app button.expand', publisher_table).live('click', function () {
                $(this).closest('tr').nextUntil('tr.app').show();
                $(this).removeClass('expand');
                $(this).addClass('collapse');
            });

            // collapse adunits
            $('tr.app button.collapse', publisher_table).live('click', function () {
                $(this).closest('tr').nextUntil('tr.app').hide();
                $(this).removeClass('collapse');
                $(this).addClass('expand');
            });
            */

            update_dashboard(true, true, true);
        },

        initializeGeo: function (bootstrapping_data) {
            initializeCommon();
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
        },

        initializeAppDetail: function (bootstrapping_data) {
            initializeCommon();
            initializeEditAppForm();
            initializeNewAdunitForm();
            initializeDeleteForm();
            initializeiOSAppSearch();
            initializeDailyCounts();
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());

            // Do Campaign Export Select stuff
            $('#publisher-app-exportSelect')
                .change(function(e) {
                    e.preventDefault();
                    var val = $(this).val();
                    if (val != 'exp') {
                    $('#appExportForm')
                            .find('#appExportType')
                            .val(val)
                            .end()
                            .submit();
                    }
                    $(this).selectmenu('index', 0);
                });

            // Hide unneeded li entry
            $('#publisher-app-exportSelect-menu').find('li').first().hide();

            fetchAppStats([bootstrapping_data.app_key]);
            fetchAdunitStats(bootstrapping_data.app_key);
        },

        initializeAdunitDetail: function (bootstrapping_data) {
            initializeCommon();
            initializeDeleteForm();
            initializeDailyCounts();
            initializeEditAdunitForm();

            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());

            $('#advertisers-testAdServer')
                .button({ icons : {secondary : 'ui-icon-circle-triangle-e'} })
                .click(function(e) {
                    e.preventDefault();
                    $('#adserverTest').dialog({
                        buttons: {
                            "Close": function() {
                                $(this).dialog("close");
                            }
                        }
                    });
                    $('#adserverTest-iFrame').attr('src',$('#adserverTest-iFrame-src').text());
                });
        },

        initializeAppCreate: function (bootstrapping_data) {
            initializeCommon();
            initializeNewAppForm();
            initializeNewAdunitForm();
        }
    };

    window.DashboardController = DashboardController;

})(this.jQuery, this.Backbone, this._);

/* REFACTOR */
var artwork_json;

// fuck you
function loadedArtwork(json) {
    if (!$('#dashboard-searchAppStore-custom-modal').dialog("isOpen"))
        return;

    $('#searchAppStore-results').html('');
    $('#searchAppStore-loading').hide();
    $('#dashboard-searchAppStore-custom-modal').dialog("close");

    artwork_json = json;
        var resultCount = json['resultCount'];
    if (resultCount == 0) {
        $('#searchAppStore-results').append("<div class='adForm-appSearch-text' />")
            .append("No results found");
        $('#dashboard-searchAppStore-custom-modal').dialog("open");
        return;
    }
    for (var i=0;i<resultCount;i++) {
        if (i > 10 ) {
            break;
        }
        var app = json['results'][i];

        $('#searchAppStore-results')
            .append($("<div class='adForm-appSearch' />")
                    .append($("<div class='adForm-appSearch-img' />")
                            .append($("<img />")
                                    .attr("src",app['artworkUrl60'])
                                    .width(40)
                                    .height(40)
                                   )
                            .append($("<span />"))
                           )
                    .append($("<div class='adForm-appSearch-text' />")
                            .append($("<span />")
                                    .append($("<a href=\"#\" onclick=\"selectArtwork("+i
                                              +");return false\";>"+app['trackName']+"</a>"))
                                    .append("<br />"+app['artistName'])
                                   )
                           )
                    .append($("<div class='clear' />"))
                   );
    }

    $('#dashboard-searchAppStore-custom-modal').dialog("open");
}

function selectArtwork(index) {
    $('#searchAppStore-results').html('');
    $('#appForm-icon').html('');
    $('#dashboard-searchAppStore-custom-modal').dialog("close");

    var app = artwork_json.results[index];
    var type = $('input:radio[name="app_type"]:checked').val();

    var form = $('app_form');
    $('#appForm input[name="name"]').val(app['trackName']);
    $('#appForm input[name="description"]').val(app['description']);
    if ( type == 'iphone' )
        $('#appForm input[name="url"]').val(app['trackViewUrl']);
    else if ( type == 'android' )
        $('#appForm input[name="package"]').val(app['trackViewUrl']);
    $('#appForm input[name="img_url"]').val(app['artworkUrl60']);
    $('#appForm select[name="primary_category"]').val(app['primaryGenreName'].toLowerCase());
    $('#appForm select[name="secondary_category"]').val(app['genres'][1].toLowerCase());

    $('#appForm-icon').append($("<img />")
                              .attr("src",app.artworkUrl60)
                              .width(40)
                              .height(40)
                              .append($("<span />")) );
}
