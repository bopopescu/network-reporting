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

(function($, Backbone, _) {


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

    /*
     * ## fetchAppsFromKeys
     * Fetches all app stats using a list of app keys and renders
     * them into table rows that have already been created in the
     * page. Useful for decreasing page load time along with `fetchAdUnitsFromAppKeys`.
     */
    function fetchAppsFromKeys (app_keys) {
        var apps = new AppCollection();
        var fetched_apps = 0;
        _.each(app_keys, function(app_key) {

            // Create a new app. When the app is fetched, we'll immediately
            // render it into its contents into a (pre-existing) table row.
            var app = new App({id: app_key, stats_endpoint: 'all'});
            app.bind('change', function(current_app) {
                var appView = new AppView({
                    model: current_app,
                    el: '#dashboard-apps'
                });
                appView.renderInline();
            });

            // Fetch the app. Try to fetch again on error (in case of
            // a 503). If it fails again, the resource is probably
            // f'ed, so pop up an error message.
            app.fetch({
                error: function() {
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
     * ## fetchAdUnitsFromAppKeys
     * Fetches AdUnit stats for an app over ajax and renders them in already
     * existing table rows. This method is useful for decreasing page load time.
     * Uses a parent app's key to bootstrap the fetch.
     */
    function fetchAdUnitsFromAppKeys (app_key) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;
        adunits.stats_endpoint = 'all';
        // Once the adunits have been fetched from the server,
        // render them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {
            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                var adunitView = new AdUnitView({ 
                    model: adunit, 
                    el: '#dashboard-apps' 
                });
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

        return adunits;
    }

    /*
     * ## initializeNewAppForm
     * Loads all click handlers/visual stuff/ajax loading for
     * the app form.
     */
    function initializeNewAppForm() {
        $('#appForm-submit')
            .click(function(e) {
                e.preventDefault();
                $('#appForm').submit();
            });

        $('#appForm input[name="app_type"]').click(function(e) {
            $('#appForm .appForm-platformDependent')
                .removeClass('iphone')
                .removeClass('android')
                .removeClass('mweb')
                .addClass($(this).val());
            if($(this).val() == 'android') {
                $('#appForm input#appForm-url').hide();
                $('#appForm input#appForm-package').show();
            }
            else {
                $('#appForm input#appForm-package').hide();
                $('#appForm input#appForm-url').show();
                if($(this).val() == 'iphone') {
                    $('#appForm input#appForm-url').attr('placeholder', 'http://itunes.apple.com/yourapp');
                }
                else {
                    $('#appForm input#appForm-url').attr('placeholder', 'http://www.yourapp.com/');
                }
            }

        }).filter(':checked').click(); // make sure we're in sync when the page Loads

        initializeiOSAppSearch();

        $('#appForm-changeIcon-link').click(function (e) {
            e.preventDefault();
            $(this).hide();
            $('#appForm-icon-upload').show();
            $('#appForm input[name="img_url"]').val('');
        });
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

        function activate ( element, container ) {
            container.find('.active').removeClass('active');
            element.addClass('active');
        }

        $("#adunit-device_format_phone").click(function(e){
            $('#adForm-tablet-container').hide();
            $('#adForm-phone-container')
                .show()
                .find('input[type="radio"]')[0].click();
            activate($(this), $(this).parent());
        });

        // Click handler for the tablet format
        $('#adunit-device_format_tablet').click(function(e){
            $('#adForm-phone-container').hide();
            $('#adForm-tablet-container')
                .show()
                .find('input[type="radio"]')[0].click();
            activate($(this), $(this).parent());
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

            }); //initialize by activating the first
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
            .click(function(e) {
                e.preventDefault();
                if ($('#dashboard-adunitEditForm').is(':visible'))
                    $('#dashboard-adunitEditForm').slideUp('fast');
                else
                    $('#dashboard-adunitEditForm').slideDown('fast');
            });

        $('#adunitEditForm-submit')
            .click(function(e) {
                e.preventDefault();
                $('#adunitEditForm-submit').addClass('disabled');
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
                $('#adunitEditForm-submit').removeClass('disabled');
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

        var search_modal = $("#appForm-search-modal").modal({
            show: false,
            keyboard: false,
            backdrop: true
        });

        var itunes_result_template = _.template($('#itunes_result-template').html());

        // Search button
        $('#appForm-search-button').click(function(e) {

            // Get all the stuff we'll need later
            var app_name_value = $("#appForm-name").val();
            var loading_stuff = $("#appForm-modal-preload");
            var results_section = $("#appForm-modal-results");

            // Show the modal
            search_modal.modal('show');

            // If they've entered some text, make the ajax call to apple
            // searching for the app they typed in. 
            if (app_name_value.length) {
                var itunes_search = $.ajax({
                    dataType: 'jsonp',
                    url: "http://itunes.apple.com/search",
                    data: {
                        term: app_name_value,
                        media: 'software'
                    }
                });

                // If we get a response, hide the loading stuff
                // and put a row in the modal for each app
                itunes_search.success(function (response) {
                    
                    loading_stuff.hide();

                    // Add all of the apps to the modal if we got 
                    // some search results.
                    if (response.resultCount > 0) {

                        var message = "Found " 
                            + response.resultCount 
                            + " results. " +
                            "Click on an app to use its data in the form.";
                        var message_div = "<div class='alert-message block-message info'>" + 
                            message + 
                            "</div>";

                        results_section.append(message_div);
                        _.each(response.results, function (result) {
                            var result_div = itunes_result_template(result);
                            results_section.append(result_div);

                            // When the div is clicked, fill the form in with the info.
                            $("#" + result.trackId).click(function() {
                                $("#appForm-name").val(result.trackName);
                                $("#appForm-url").val(result.trackViewUrl);
                                $('#appForm input[name="img_url"]')
                                    .val(result.artworkUrl60);
                                
                                if (result.hasOwnProperty('primaryGenreName')) {
                                    $('#appForm select[name="primary_category"]')
                                        .val(result.primaryGenreName.toLowerCase());
                                }
                                if (result.genres[1] !== undefined) {
                                    $('#appForm select[name="secondary_category"]')
                                        .val(result.genres[1].toLowerCase());
                                }

                                // This doesn't do anything to the form data but
                                // it makes the icon appear to have been uploaded.
                                $('#appForm-icon').html('').append(
                                    $("<img />")
                                        .attr("src", result.artworkUrl60)
                                        .width(40)
                                        .height(40)
                                );

                                search_modal.modal('hide');
                            });

                        });
                    } else {
                        var message = "No apps matching this name or description were " +
                            "found in the App Store.";
                        var message_div = "<div class='alert-message block-message'>" + 
                            message + 
                            "</div>";
                        results_section.append(message_div);
                    }

                });
                
                // If we got an error it's probably because we can't connect
                itunes_search.error(function () {
                    var message = "We were unable to connect to the App Store to find your app. " +
                        "Sorry for the inconvenience.";
                        var message_div = "<div class='alert-message block-message error'>" + 
                            message + 
                            "</div>";
                        results_section.append(message_div);
                });
                
            } else {
                // Hide the loading stuff, but show a "you did it wrong" message
                loading_stuff.hide();
                var message = "Please enter your app's name in the 'App name' " +
                    "field so we can search the App Store.";
                var message_div = "<div class='alert-message block-message'>" + 
                    message + 
                    "</div>";
                results_section.append(message_div);

            }

            // Reset the defaults when the modal is hidden again
            search_modal.on('hide', function(){
                loading_stuff.show();
                results_section.html("");
            });

        });
    }

    /*
     * # initializeCommon
     * This function groups together a couple of pieces of functionality that are used on
     * all of the publisher pages (inventory, app, adunit stuff)
     */
    function initializeCommon() {

        // Use breakdown to switch charts
        $('.stats-breakdown tr').click(function(e) {
            $('#dashboard-stats-chart').fadeOut(100, function() {
                mopub.Chart.setupDashboardStatsChart('area');
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


    /*
     * ## Dashboard Controller
     */
    var DashboardController = {

        initializeIndex: function (bootstrapping_data) {

            // Adds click handlers for the top date buttons and stats breakdown
            // date buttons, and click handlers for the stats breakdown graph-
            // changing
            initializeCommon();

            // Fetch all of the app stats from their keys. When all apps
            // are finished loading, we render the chart.
            var apps = fetchAppsFromKeys(bootstrapping_data.app_keys);
            apps.bind('loaded', function() {

                // Load the chart
                var chart_view = new CollectionChartView({
                    collection: apps,
                    start_date: bootstrapping_data.start_date,
                    display_values: ['req', 'imp', 'clk']
                });
                chart_view.render();
            });

            // Fetch all of the adunit stats for each app. After fetch,
            // the table row for the adunit will be rendered
            _.each(bootstrapping_data.app_keys, function(app_key) {
                var new_adunits = fetchAdUnitsFromAppKeys(app_key);
            });

            // Set up the quick jump dropdown
            $("#app-quick-navigate").chosen().change(function() {
                window.location = $(this).val();
            });

        },

        initializeAppDetail: function (bootstrapping_data) {
            initializeCommon();
            initializeEditAppForm();
            initializeNewAdunitForm();
            initializeDeleteForm();
            initializeiOSAppSearch();

            var apps = fetchAppsFromKeys([bootstrapping_data.app_key]);
            fetchAdUnitsFromAppKeys(bootstrapping_data.app_key);

            apps.bind('loaded', function() {

                var chart_view = new CollectionChartView({
                    collection: apps,
                    start_date: bootstrapping_data.start_date,
                    display_values: ['rev', 'imp', 'cpm' ] //TODO include cpm
                });
                chart_view.render();

                // Load the daily counts
                var daily_counts_view = new DailyCountsView({
                    model: apps.models[0]
                });
                daily_counts_view.render();

            });

        },

        initializeAdunitDetail: function (bootstrapping_data) {
            initializeCommon();
            initializeDeleteForm();
            initializeEditAdunitForm();
            
            // This usually happens in the model. We're doing it here
            // so as not to step on other people's feet. This eventually
            // should be changed to enforce some consistency.
            _.extend(AdUnit.prototype, StatsMixin);

            $('#advertisers-testAdServer').click(function(e) {
                e.preventDefault();
                $('#adserverTest').dialog({
                    buttons: {
                        "Close": function() {
                            $(this).dialog("close");
                        }
                    }
                });
                $('#adserverTest-iFrame')
                    .attr('src', $('#adserverTest-iFrame-src').text());
            });

            var adunit = new AdUnit();
            adunit.id = bootstrapping_data.adunit_key;
            adunit.app_id = bootstrapping_data.app_key;
            
            adunit.bind('change', function () {

                // fuck you
                var adunits = new AdUnitCollection();                
                adunits.add(adunit);
                _.extend(AdUnitCollection.prototype, StatsMixin);

                // Render the chart
                var chart_view = new CollectionChartView({
                    collection: adunits,
                    start_date: bootstrapping_data.start_date,
                    display_values: ['rev', 'imp', 'cpm' ] 
                });
                chart_view.render();

                // Render the daily counts
                var daily_counts_view = new DailyCountsView({
                    model: adunit
                });
                daily_counts_view.render();

            });

            adunit.fetch();            

        },

        initializeAppCreate: function (bootstrapping_data) {
            initializeCommon();
            initializeNewAppForm();
            initializeNewAdunitForm();
        }
    };

    window.DashboardController = DashboardController;

})(this.jQuery, this.Backbone, this._);