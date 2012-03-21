(function ($, mopub) {
    "use strict";

    /*
     * # Utility functions
     */

    function initializeDateButtons() {
        // set up stats breakdown dateOptions
        $('#stats-breakdown-dateOptions input').click(function() {
            $('.stats-breakdown-value').hide();
            $('.stats-breakdown-value.'+$(this).val()).show();
        });
    }

    function renderCampaign(campaign) {

        var campaign_view = new CampaignView({
            model: campaign,
            el: 'orders_table'
        });
        campaign_view.renderInline();

        var adgroups = new AdGroupCollection(campaign.get('adgroups'));
        adgroups.each(function(adgroup){
            renderAdGroup(adgroup);
        });
    }

    function renderAdGroup(adgroup)  {
        var adgroup_view = new AdGroupView({
            model: adgroup,
            el: 'orders_table'
        });
        adgroup_view.renderInline();
    }

    function renderApp(app) {
        var app_view = new AppView({
            model: app,
            el: 'orders_table'
        });
        app_view.renderInline();

        // var adunits = new AdUnitCollection(app.get('adunits'));
        // adunits.each(function(adunit){
        //     renderAdUnit(adunit)
        // });
    }

    function renderAdUnit(adunit) {
        var adunit_view = new AdUnitView({
            model: adunit,
            el: 'orders_table'
        });
        adunit_view.renderInline();
    }

    function renderChart(stats, start_date) {
        mopub.dashboardStatsChartData = {
            pointStart: start_date,
            pointInterval: 86400000,
            requests: [{ "Total": stats.requests }],
            impressions: [{ "Total": stats.impressions }],
            clicks: [{ "Total": stats.clicks }],
            users: [{ "Total": stats.users }]
        };

        mopub.Chart.setupDashboardStatsChart('area');

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
    }

    function changeStatus(adgroups, status) {

        _.each(adgroups, function(adgroup) {
            $("#" + adgroup + "-img").removeClass('hidden');
        });

        var status_promise = $.post('/advertise/orders/status/', {
            line_items: adgroups,
            status: status
        });

        // On success, hide the loading spinner and change the status
        // icon appropriately.
        status_promise.success(function(){
            _.each(adgroups, function(adgroup) {

                // Hide the loading image 
                $("#" + adgroup + "-img").toggleClass('hidden');

                var status_img = $('#status-' + adgroup);
                var status_change_controls = $('.status_change_control');
                var lineitem_tds = $('#lineitem-' + adgroup + ' td:not(.controls)');
                if (status == 'play' || status == 'run') {
                    $(lineitem_tds).fadeTo(500, 1);
                    $('#lineitem-' + adgroup).removeClass('archived');
                    $(status_img).attr('src', '/images/active.gif');

                } else if (status == 'pause') {
                    $(lineitem_tds).fadeTo(500, 0.2);
                    $(status_img).attr('src', '/images/paused.gif');

                } else if (status == 'archive') {
                    $('#lineitem-' + adgroup).addClass('archived');
                    $(lineitem_tds).fadeTo(500, 0.2);
                    $(status_img).attr('src', '/images/archived.gif');

                } else if (status == 'delete') {
                    $(lineitem_tds).fadeTo(500, 0.2);
                    $(status_img).attr('src', '/images/deleted.gif');
                }
            });
 
        });

        status_promise.error(function () {
            _.each(adgroups, function(adgroup) {
                $("#" + adgroup + "-img").addsClass('hidden');
            });
        });
    }

    // Sets up the status control event handlers
    function initializeStatusControls() {
        $(".status_change.btn").click(function(e){
            e.preventDefault();
            var status = $(this).attr('data-toggle');
            var checked_adgroups = $(".status_change_control:checked");
            var keys = _.map(checked_adgroups, function (row) {
                return $(row).attr('id');
            });

            changeStatus(keys, status);

        });
    }

    function toggleArchiveButton() {
        var archive_button = $("#archive-button");

        // If the archived line items are hidden,
        // show them. The `state-hide` class indicates that
        // the archived line items are hidden.
        if (archive_button.hasClass('state-hide')) {
            $('.archived').removeClass('hidden');
            archive_button.removeClass('state-hide');

        // If the archived line items are showing,
        // hide them. If `state-hide` is missing, it means
        // they're showing, so we add it back in once we've
        // hidden them. 
        } else {
            $('.archived').addClass('hidden');
            archive_button.addClass('state-hide');
        }

        // Flip the icon and text in the button.
        $(".button-text-icon", archive_button).toggleClass('hidden');
    }


    var OrdersController = {
        initializeIndex: function(bootstrapping_data) {
            initializeStatusControls();
            $("#archive-button").click(toggleArchiveButton);

            // Create a campaign collection for the account
            var campaigns = new CampaignCollection();
            campaigns.stats_endpoint = 'direct';

            // Once the campaigns have been fetched, render them.
            campaigns.bind('reset', function(campaigns_collection) {
                _.each(campaigns.models, function(campaign) {
                    renderCampaign(campaign);
                });
            });

            // Fetch the campaigns
            campaigns.fetch();
        },

        initializeOrderDetail: function(bootstrapping_data) {
            initializeStatusControls();
            initializeDateButtons();
            
            var validator = $('form#order_form').validate({
                errorPlacement: function(error, element) {
                    element.closest('div').append(error);
                },
                submitHandler: function(form) {
                    $(form).ajaxSubmit({
                        data: {ajax: true},
                        dataType: 'json',
                        success: function(jsonData, statusText, xhr, $form) {
                            if(jsonData.success) {
                                window.location.reload();
                                $('form#order_form #submit').button({
                                    label: 'Success...',
                                    disabled: true
                                });
                            } else {
                                validator.showErrors(jsonData.errors);
                                $('form#order_form #submit').button({
                                    label: 'Try Again',
                                    disabled: false
                                });
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            $('form#order_form #submit').button({
                                label: 'Try Again',
                                disabled: false
                            });
                        },
                        beforeSubmit: function(arr, $form, options) {
                            $('form#order_form #submit').button({
                                label: 'Submitting...',
                                disabled: true
                            });
                        }
                    });
                }
            });

            // Fill in stats for the campaign/adgroup table
            var campaign = new Campaign({
                id: bootstrapping_data.order_key,
                stats_endpoint: 'direct'
            });

            campaign.bind('change', function(current_campaign) {
                renderCampaign(campaign);
            });

            campaign.fetch();

            renderChart(bootstrapping_data.daily_stats,
                        bootstrapping_data.start_date);


            // Fill in stats for the targeting table
            _.each(bootstrapping_data.targeted_apps, function(app_key) {
                var app = new App({
                    id: app_key,
                    stats_endpoint: 'direct'
                });

                app.url = function () {
                    var stats_endpoint = this.get('stats_endpoint');
                    return '/api/campaign/'
                        + bootstrapping_data.order_key
                        + '/app/'
                        + this.id
                        + "?"
                        + window.location.search.substring(1)
                        + '&endpoint='
                        + stats_endpoint;
                };

                app.bind('change', function(current_app){
                    renderApp(current_app);
                });
                app.fetch();
            });

            _.each(bootstrapping_data.targeted_adunits, function(adunit_key) {
                var adunit = new AdUnit({
                    id: adunit_key,
                    stats_endpoint: 'direct'
                });

                adunit.url = function () {
                    var stats_endpoint = this.get('stats_endpoint');
                    return '/api/campaign/'
                        + bootstrapping_data.order_key
                        + '/adunit/'
                        + this.id
                        + "?"
                        + window.location.search.substring(1)
                        + '&endpoint='
                        + stats_endpoint;
                };

                adunit.bind('change', function(current_adunit){
                    console.dir(current_adunit);
                    renderAdUnit(current_adunit);
                });
                
                adunit.fetch();
            });

            // Sets up the click handler for the order form
            $("a#order_form_edit").click(function(e){
                e.preventDefault();
                $("#order_form_container").show();
            });

            // submit button
            $('form#order_form #submit').click(function(e) {
                e.preventDefault();
                $('form#order_form').submit();
            });
        },

        initializeLineItemDetail: function(bootstrapping_data) {
            renderChart(bootstrapping_data.daily_stats,
                        bootstrapping_data.start_date);
            initializeDateButtons();
        },

        initializeOrderAndLineItemForm: function(bootstrapping_data) {
            var validator = $('form#order_and_line_item_form').validate({
                errorPlacement: function(error, element) {
                    element.closest('div').append(error);
                },
                submitHandler: function(form) {
                    $(form).ajaxSubmit({
                        data: {ajax: true},
                        dataType: 'json',
                        success: function(jsonData, statusText, xhr, $form) {
                            if(jsonData.success) {
                                window.location = jsonData.redirect;
                                $('form#order_and_line_item_form #submit').button({
                                    label: 'Success...',
                                    disabled: true
                                });
                            } else {
                                validator.showErrors(jsonData.errors);
                                $('form#order_and_line_item_form #submit').button({
                                    label: 'Try Again',
                                    disabled: false
                                });
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            $('form#order_and_line_item_form #submit').button({
                                label: 'Try Again',
                                disabled: false
                            });
                        },
                        beforeSubmit: function(arr, $form, options) {
                            $('form#order_and_line_item_form #submit').button({
                                label: 'Submitting...',
                                disabled: true
                            });
                        }
                    });
                }
            });

            // submit button
            $('form#order_and_line_item_form #submit').button({
                icons: {secondary: 'ui-icon-circle-triangle-e'}
            });
            $('form#order_and_line_item_form #submit').click(function(e) {
                e.preventDefault();
                $('form#order_and_line_item_form').submit();
            });

            // toggle fields based on adgroup_type
            $('select[name="adgroup_type"]').change(function() {
                var adgroup_type = $(this).val();
                $('.adgroup_type_dependant').each(function() {
                    $(this).toggle($(this).hasClass(adgroup_type));
                });
            }).change(); // update on document ready

            // help links
            // TODO: make sure all of these are necessary, rename?
            $('a[id$="-helpLink"]').click(function(e) {
                e.preventDefault();
                $('#' + $(this).attr('id').replace('-helpLink', '-helpContent')).dialog({
                    buttons: { "Close": function() { $(this).dialog("close"); } }
                });
            });

            // date controls
            $('input[type="text"].date').datepicker({minDate: 0});

            function makeValidTime(timeStr, defHour, defMin, defAmPm) {
                // Checks to see if a timeStr is valid, returns valid form
                // AM/PM (and variants) are optional.

                var timePat = /^(\d{1,2}):(\d{2})(\s?(AM|am|PM|pm|aM|pM|Pm|Am))?$/;

                if (defMin < 10) {
                    defMin = '0' + defMin;
                }
                var matchArray = timeStr.match(timePat);
                if (matchArray == null) {
                    return defHour + ':' + defMin + ' ' + defAmPm;
                }

                var hour = matchArray[1];
                var minute = matchArray[2];
                var ampm = matchArray[4];

                // Handle military time stuff
                if (hour >= 12 && hour <= 23) {
                    hour = hour - 12;
                    // 12:00 AM to 12:00 PM
                    // 12:00    to 12:00 PM
                    //
                    // 15:00 AM to 3:00 PM
                    // 15:00 PM to 3:00 PM
                    // 15:00    to 3:00 PM
                    if (hour == 0) {
                        hour = 12;
                        if (ampm === undefined) {
                            ampm = 'PM';
                        }
                    }
                    else {
                        ampm = 'PM';
                    }
                }

                if (hour == 0) {
                    ampm = 'AM';
                    hour = 12;
                }
                // Set invalid times to 0 minutes and 12 hours and default to AM
                if (minute < 0 || minute > 59) {
                    minute = defMin;
                }
                if (hour < 0 || hour > 23) {
                    hour = defHour;
                }
                if (ampm === undefined) {
                    ampm = defAmPm;
                }

                else {
                    ampm = ampm.toUpperCase();
                }
                return hour + ':' + minute + ' ' + ampm ;
            }

            $('input[name="start_datetime_0"]').change(function(e) {
                e.preventDefault();
                var val = $(this).val();
                if (val != '') {
                    $('input[name="start_datetime_1"]').change();
                }
            });

            $('input[name="end_datetime_0"]').change(function(e) {
                e.preventDefault();
                var val = $(this).val();
                if (val != '') {
                    $('input[name="end_datetime_1"]').change();
                }
            });

            $('input[name$="_datetime_1"]').change(function(e){
                e.preventDefault();
                var name = $(this).attr('name');
                var val = $(this).val();
                if (name == 'start_datetime_1') {
                    if($('input[name="start_datetime_0"]').val() == '') {
                        val = '';
                    } else {
                        val = makeValidTime(val, 12, 0, 'AM');
                    }
                }
                else if (name == 'end_datetime_1') {
                    if($('input[name="end_datetime_0"]').val() == '') {
                        val = '';
                    } else {
                        val = makeValidTime(val, 11, 59, 'PM');
                    }
                }
                $(this).val(val);
            });

            $('input[name="end_datetime_0"], input[name="end_datetime_1"], select[name="budget_type"], select[name="budget_strategy"]').change(function(){
                if(!$('input[name="end_datetime_0"]').val() &&
                   !$('input[name="end_datetime_1"]').val() &&
                   $('select[name="budget_type"]').val() == 'full_campaign') {
                    $('input#id_budget_strategy_1').prop('checked', 'checked');
                    $('input#id_budget_strategy_0').removeProp('checked');
                    $('input#id_budget_strategy_0').attr('disabled', 'disabled');
                }
                else {
                    $('input#id_budget_strategy_0').removeAttr('disabled');
                }
            }).change();

            $('#all-adunits').change(function() {
                // select or deselect all adunits
                $('input[name="site_keys"]').prop('checked', $(this).prop('checked'));
            });

            // device targeting
            $('input[name="device_targeting"]').change(function() {
                if($(this).val() == '0') {
                    $('#device_targeting').slideUp();
                }
                else {
                    $('#device_targeting').slideDown();
                }
            });
            // update on document ready
            if($('input[name="device_targeting"]:checked').val() == '0') {
                $('#device_targeting').hide();
            }

            // change form based on bid_strategy
            $('select[name="bid_strategy"]').change(function() {
                var bid_strategy = $(this).val();
                var budget_type_options = $('select[name="budget_type"] option');
                if(bid_strategy == 'cpm') {
                    budget_type_options[0].innerHTML = 'impressions/day';
                    budget_type_options[1].innerHTML = 'total impressions';
                }
                else {
                    budget_type_options[0].innerHTML = 'USD/day';
                    budget_type_options[1].innerHTML = 'total USD';
                }
            }).change(); // update on document ready

            $('select[name="budget_type"]').change(function() {
                var budget_type = $(this).val();
                $('.budget_type_dependent').each(function() {
                    $(this).toggle($(this).hasClass(budget_type));
                });
            }).change(); // update on document ready

            // Toggling for advanced options
            $('#toggle_advanced')
                .button('option', {icons: { primary: 'ui-icon-triangle-1-s' }})
                .click(function(e) {
                    e.preventDefault();
                    var buttonTextElem = $('.ui-button-text', this);
                    if ($('fieldset#advanced').is(':hidden')) {
                        $('fieldset#advanced').slideDown('fast');
                        $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
                        $('.ui-button-text', this).text('Hide Advanced Details');
                    } else {
                        $('fieldset#advanced').slideUp('fast');
                        $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
                        $('.ui-button-text', this).text('Show Advanced Details');
                    }
                }); // TODO: need to update on document ready

            /* GEO TARGETING */
            var geo_s = 'http://api.geonames.org/searchJSON?username=MoPub&';
            var pre = {type: 'country', data: []};
            var city_pre = {type: 'city', data: []};
            //Not being used right now
            //var state_pre = {type: 'state', data: []};

            for(var index in countries) {
                var dat = countries[index];
                if($.inArray(dat.code, bootstrapping_data.priors) != -1) {
                    pre.data.push(dat);
                }
                if(pre.length == bootstrapping_data.priors.length)
                    break;
            }

            //city is ll:ste:name:ccode;
            for(var i in bootstrapping_data.city_priors) {
                if(bootstrapping_data.city_priors.hasOwnProperty(i)) {
                    var datas = bootstrapping_data.city_priors[i].split(':');
                    var ll = datas[0].split(',');
                    var ste = datas[1];
                    var name = datas[2];
                    var ccode = datas[3];
                    city_pre.data.push(
                        { lat: ll[0],
                          lng: ll[1],
                          countryCode: ccode,
                          adminCode1: ste,
                          name: name
                        });
                }
            }

            //Need to create data object that is array of dictionary [ {name, id} ]
            $('#geo_pred_ta').tokenInput(null, {
                    data: countries,
                hintText: 'Type in a country name',
                formatResult: function( row ) {
                    return row.name;
                },
                formatMatch: function( row, i, max ){
                    return [row.name, row.code];
                },
                prePopulate: pre
            });

            $('#city_ta').tokenInput(geo_s, {
                country: 'US',
                doImmediate: false,
                hintText: 'Type in a city name',
                queryParam: 'name_startsWith',
                featureClass: 'P',
                prePopulate: city_pre,
                contentType: 'json',
                type: 'city',
                minChars: 3,
                method: 'get'
            });
            //Verify that all cities in city_pre are in the SINGLE country that is pre

            /* Not doing states atm
               $('#state_ta').tokenInput(geo_s, {
               country: 'US',
               doImmediate: false,
               queryParam: 'name_startsWith',
               featureCode: 'ADM1',
               contentType: 'json',
               prePopulate: state_pre,
               type: 'state',
               minChars: 5,
               method: 'get'
               }); */

            // Show location-dependent fields when location targeting is turned on
            $('input[name="region_targeting"]').click(function(e) {
                var loc_targ = $(this).val();
                $('.locationDependent').hide();
                $('.' + loc_targ + '.locationDependent').show();
                if ($(this).val() == 'all') {
                    $('li.token-input-city span.token-input-delete-token').each(function() {
                        $(this).click();
                    });
                }
            }).filter(':checked').click();
        }
    };

    mopub.Controllers.OrdersController = OrdersController;

})(window.jQuery, window.mopub || { Controllers: {} });
