$(function() {
    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    function initialize_campaign_data(campaign_data, include_adunits, ajax_query_string) {
        // create mopub campaign
        // endpoint=all
        var mopub_campaign = new Campaign(campaign_data);

        var all_campaigns = [mopub_campaign];

        // create network campaign
        // endpoint=network
        if (campaign_data.reporting) {
            // Create copy of campaign_data
            var network_campaign_data = jQuery.extend({}, campaign_data);
            network_campaign_data.stats_endpoint = 'networks';
            var network_campaign = new Campaign(network_campaign_data);

            all_campaigns.push(network_campaign);
        }

        // Create CampaignView and fetch mopub campaign and network
        // campaign if campaign has reporting
        _.each(all_campaigns, function(campaign) {
            new CampaignView({
                model: campaign
            });

            campaign.fetch({ data: ajax_query_string, });
        });

        // Load NetworkApps Collections
        var network_apps = new NetworkApps();
        if (include_adunits) {
            network_apps.type = 'adunits';
        }
        network_apps.campaign_key = campaign_data.id;

        var network_apps_view = new NetworkAppsView({
            collection: network_apps
        });
        network_apps.fetch({ data: ajax_query_string, });

        return all_campaigns;
    }

    var show_network_chart_data = true;
    var initialize_show_network = function() {
        // Use breakdown to switch charts
        $('.stats-breakdown tr').click(function(e) {
            $('#dashboard-stats .stats-breakdown .active').removeClass('active');
            $(this).addClass('active');
            $('#dashboard-stats-chart').fadeOut(100, function() {
                mopub.Chart.setupDashboardStatsChart('line');
                if (!show_network_chart_data) {
                    if (mopub.Chart.trafficChart.series.length != 1) {
                        mopub.Chart.trafficChart.series[1].hide();
                    }
                }
                $(this).show();
                });
            });

        $('#show-network').change(function() {
            if ($(this).is(':checked')) {
                $.cookie("show-network-data", "true");
                $('.network-data').show();
                $('.network-chart-data').show();
                $('.mopub-chart-data').hide();
                if (mopub.Chart.trafficChart) {
                    if (mopub.Chart.trafficChart.series.length != 1) {
                        mopub.Chart.trafficChart.series[1].show();
                    }
                    show_network_chart_data = true;
                }
            } else {
                $.cookie("show-network-data", null);
                $('.network-data').hide();
                $('.network-chart-data').hide();
                $('.mopub-chart-data').show();
                function hide_network_trafficChart_series() {
                    if (mopub.Chart.trafficChart) {
                        if (mopub.Chart.trafficChart.series.length != 1) {
                            mopub.Chart.trafficChart.series[1].hide();
                        }
                        show_network_chart_data = false;
                    } else {
                        setTimeout(hide_network_trafficChart_series, 50);//wait 50 millisecnds then recheck
                    }
                }
                hide_network_trafficChart_series()
            }
        });

        if (!$.cookie("show-network-data")) {
            $('#show-network').click();
        } else {
            $('#show-network').change();
        }
    }

    var NetworksController = { 
        initialize: function(bootstrapping_data) {
            var campaigns_data = bootstrapping_data.campaigns_data,
                date_range = bootstrapping_data.date_range,
                graph_start_date = bootstrapping_data.graph_start_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                networks = bootstrapping_data.networks,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            initializeDateButtons();

            var all_campaigns = [];
            _.each(campaigns_data, function(campaign_data) {
                all_campaigns = all_campaigns.concat(initialize_campaign_data(campaign_data, false, ajax_query_string));
            });

            var campaigns = new Campaigns(all_campaigns);

            // Load chart
            var graph_view = new NetworkGraphView({
                collection: campaigns,
                today: today,
                yesterday: yesterday,
                date_range: date_range,
                start_date: graph_start_date,
                line_graph: false,
                mopub_optimized: false,
            });

            initialize_show_network();

            $('.show-apps').click(function() {
                var key = $(this).attr('id');
                var div = $('.' + key + '-apps-div');
                if (div.is(':hidden')) {
                    div.show();
                    $(this).children('span').text("Hide Apps");
                } else {
                    div.hide()
                    $(this).children('span').text("Show Apps");
                }
            });

            $('#network-editSelect').change(function() {
                if ($(this).val()) {
                    window.location = $(this).val();
                }
                $(this).selectmenu('index', 0);
            });

            $('#network-editSelect-menu').find('li').first().hide();

            //move to a utils package
            // checks if email is valid
            function isValidEmailAddress(emailAddress) {
                var pattern = new RegExp(/^(\s*)(("[\w-+\s]+")|([\w-+]+(?:\.[\w-+]+)*)|("[\w-+\s]+")([\w-+]+(?:\.[\w-+]+)*))(@((?:[\w-+]+\.)*\w[\w-+]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$)|(@\[?((25[0-5]\.|2[0-4][\d]\.|1[\d]{2}\.|[\d]{1,2}\.))((25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\.){2}(25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\]?$)/i);
                return pattern.test(emailAddress);
            };

            // taken from mopub-dashboard.js #appEditForm (could be combined)
            $('#networkSettingsForm-submit')
                .button({
                    icons: { secondary: "ui-icon-circle-triangle-e" }
                })

                .click(function(e) {
                    e.preventDefault();
                    $('#networkSettingsForm-loading').show();
                    $('#settings-form-message').hide();

                    // check if all emails are valid
                    var valid = true;
                    var list = $('#network-settingsForm textarea').val().split(',');
                    for (var i = 0; i < list.length; i++) {
                        if (!isValidEmailAddress(list[i])) {
                            valid = false;
                        }
                    }

                    if (valid) {
                        $.ajax({
                            type: 'POST',
                            url: '/ad_network_reports/settings/',
                            data : $('#networkForm').serialize(),
                            success : function(resp) {
                                $('#networkSettingsForm-loading').hide();
                                $('#network-settingsForm').slideUp('fast');
                            },
                            error : function(jqXHR, textStatus, errorThrown) {
                                $('#settings-form-message').html("Couldn't update settings.");
                                $('#settings-form-message').show();
                                $('#networkSettingsForm-loading').hide();
                            }
                        });
                    } else {
                        $('#settings-form-message')
                            .html("Please enter a valid email address or a list of valid email addresses.");
                        $('#settings-form-message').show();
                        $('#networkSettingsForm-loading').hide();
                    }
                });

            $('#networkSettingsForm-cancel')
                .click(function(e) {
                    e.preventDefault();
                    $('#network-settingsForm').slideUp('fast');
                });

            $('#network-settingsButton')
                .button({ icons: { primary: "ui-icon-wrench" } })
                .click(function(e) {
                    e.preventDefault();
                    if ($('#network-settingsForm').is(':visible')) {
                        $('#network-settingsForm').slideUp('fast');
                    } else {
                        $('#network-settingsForm').slideDown('fast');
                    }
                });
        }
    }

    var EditNetworkController = {
        initialize: function(bootstrapping_data) {
            var network_type = bootstrapping_data.network_type,
                pretty_name = bootstrapping_data.pretty_name,
                account_key = bootstrapping_data.account_key,
                adunits = bootstrapping_data.adunits,
                priors = bootstrapping_data.priors,
                city_priors = bootstrapping_data.city_priors,
                login_state = bootstrapping_data.login_state,
                LoginStates = bootstrapping_data.LoginStates;
            
            var saved_new_login = false;

            // make necessary changes based on network type
            var pub_ids = {
                'admob': 'admob_pub_id',
                'adsense': 'adsense_pub_id',
                'brightroll': 'brightroll_pub_id',
                'ejam': 'ejam_pub_id',
                'inmobi': 'inmobi_pub_id',
                'jumptap': 'jumptap_pub_id',
                'millennial': 'millennial_pub_id',
                'mobfox': 'mobfox_pub_id'
            };

            var pub_id = pub_ids[network_type];

            $('.app-pub-id')
                .keyup(function () {
                    var value = $(this).val();
                    var div = $(this).parents('tbody');
                    $(div).find('input[name$="'+pub_id+'"]').each(function () {
                        if (!$(this).hasClass('initialized')) {
                            $(this).val(value);
                        }
                        if ($(this).is(':hidden')) {
                            $(this).siblings('span.pub_id.muted.adunit').each(function () {
                                $(this).text(value);
                                if (value) {
                                    $(this).show();
                                    $(this).siblings('span.pub_id').show();
                                } else {
                                    $(this).hide();
                                    $(this).siblings('span.pub_id').hide();
                                }
                            });
                        }
                    });
                    // Hide any tooltips

                    (value) ? $(this).tooltip('hide') : $(this).tooltip('show');
                })
                .focusout(function () {
                    if ($(this).val()) {
                        var div = $(this).parents('tbody');
                        $(div).find('input[name$="'+pub_id+'"]').each(function () {
                            $(this).addClass('initialized');
                        });
                    }
                    });


            // set up popovers to copy all cpms
            _.each(adunits, function(key) {
                var app_key = key[0];
                var adunit_key = key[1];
                $('#id_' + adunit_key + '-bid')
                    .popover({html: true,
                        content: function() {
                            return _.template($('#popover-content').html(), {
                                adunit_key: adunit_key,
                                app_key: app_key,
                            });
                        },
                        template: _.template($('#popover-template').html(), {}),
                        placement: 'left',
                        trigger: 'focus'});
                    });

            // set up active checkbox's for app level
            $('.all-adunits').click(function() {
                var key = $(this).attr('id').replace('-all-adunits', '');
                if ($(this).is(':checked')) {
                    $('.' + key + '-adunit').attr("checked", "checked");
                } else {
                    $('.' + key + '-adunit').removeAttr("checked");
                }
                // Close the help tooltip
                if (starting_tooltip) {
                    starting_tooltip.tooltip('hide');
                    starting_tooltip = null;
                }
                // If no ad network ID set up, show a tooltip
                if ($(this).is(':checked')) {
                    var network_input = $(this).parents('tr').find('input[name$="'+pub_id+'"]');
                    var value = network_input.val();
                    if (!value) {
                        network_input.tooltip({
                            title: 'Enter the network ID to enable (<a href="#">help!</a>)',
                            trigger: 'manual',
                            placement:'top'
                        });
                        network_input.tooltip('show');
                    }
                }
                else {
                    $(this).parents('tr').find('input[name$="'+pub_id+'"]').tooltip('hide');
                }
            });

            $('input[class$="adunit"]').click(function() {
                // Close the help tooltip
                if (starting_tooltip) {
                    starting_tooltip.tooltip('hide');
                    starting_tooltip = null;
                }
            });
                

            // set cpms when copy all cpm button is clicked for either 14 day
            // or 7 day
            _.each(['7-day', '14-day'], function(days) {
                $('#copy-' + days).click(function() {
                    $('.' + days + '-cpm').each(function() {
                        var key = $(this).attr('id').replace('-' + days, '');
                        var cpm = parseFloat($(this).text().replace('$', '')).toString();
                        $('.' + key + '-field').val(cpm);
                        });
                    });
                $('.copy-' + days).click(function() {
                    var key = $(this).attr('id').replace('copy-' + days + '-', '');
                    var cpm = parseFloat($(this).parent().text().replace('$', '')).toString();
                    $('.' + key + '-field').val(cpm);
                    });
                });

            // set up 'show advanced settings' button
            $('#advanced')
                .button('option', {icons: { primary: 'ui-icon-triangle-1-s' }})
                .click(function() {
                    if ($('.advanced').is(':hidden')) {
                        $('.advanced').slideDown();
                        $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
                        $('.ui-button-text', this).text('Hide Advanced Settings');
                    } else {
                        $('.advanced').slideUp();
                        $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
                        $('.ui-button-text', this).text('Show Advanced Settings');
                    }
                });

            // TODO: merge this with controllers/campaigns.js form
            function setupNetworkForm() {
                // select the appropriate campaign_type from the hash
                if (window.location.hash.substring(1) !== '') {
                    $('select[name="campaign_type"]').val(window.location.hash.substring(1));
                }

                var validator = $('form#campaign_and_adgroup').validate({
                    errorPlacement: function(error, element) {
                        element.closest('div').append(error);
                    },
                    submitHandler: function(form) {
                        $(form).ajaxSubmit({
                            data: {ajax: true, show_login: !$('#networkLoginForm').is(':hidden')},
                            dataType: 'json',
                            success: function(jsonData, statusText, xhr, $form) {
                                if(jsonData.success) {
                                    if (saved_new_login && login_state == LoginStates.NOT_SETUP) {
                                        data = "&account_key=" + account_key + "&network=" + network_type + '&req_type=pull';

                                        $.ajax({url: 'https://checklogincredentials.mopub.com',
                                            data: data,
                                            crossDomain: true,
                                            dataType: "jsonp",
                                        });
                                    }
                                    window.location = jsonData.redirect;
                                    $('form#campaign_and_adgroup #submit').button({
                                        label: 'Success...',
                                        disabled: true
                                    });
                                } else {
                                    console.log(jsonData.errors);
                                    validator.showErrors(jsonData.errors);
                                    $('form#campaign_and_adgroup #submit').button({
                                        label: 'Try Again',
                                        disabled: false
                                    });
                                }
                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                $('form#campaign_and_adgroup #submit').button({
                                    label: 'Try Again',
                                    disabled: false
                                });
                            },
                            beforeSubmit: function(arr, $form, options) {
                                $('form#campaign_and_adgroup #submit').button({label: 'Submitting...',
                                                                               disabled: true});
                            }
                        });
                    }
                });
            }

            setupNetworkForm();

            $('form#campaign_and_adgroup #submit')
                .button({ icons : { secondary : 'ui-icon-circle-triangle-e' } })
                .click(function(e) {
                    e.preventDefault();
                    $('form#campaign_and_adgroup').submit();
                });


            $("#networkLoginForm-submit").click(function() {
                    // Hack to serialize sub-section of forms data.
                    // Add a new form and hide it.
                    $('#campaign_and_adgroup').append('<form id="form-to-submit" style="visibility:hidden;"></form>');
                    // Clone the fieldset into the new form.
                    $('#form-to-submit').html($('.login-credentials-fields').clone());
                    // Serialize the data.
                    var data = $('#form-to-submit').serialize();
                    // Remove the form.
                    $('#form-to-submit').remove();
                    data += ("&account_key=" + account_key + "&network=" + network_type + '&req_type=check');

                    // Check if data submitted in the form is valid login
                    // information for the ad network
                    var message = $('.login-credentials-message');
                    $(message).html("Verifying login credentials...");

                    $.ajax({url: 'https://checklogincredentials.mopub.com',
                        data: data,
                        crossDomain: true,
                        dataType: "jsonp",
                        success: function(valid) {
                            // Upon success notify the user
                            if (valid) {
                                $(message).html("MoPub is currently optimizing "
                                                + pretty_name
                                                + " by pulling data from "
                                                + pretty_name + " using the following credentials.");
                                var username = $('#id_username_str').val();
                                var password = $('#id_password_str').val();
                                var client_key = $('#id_client_key').val();

                                $('#id_username_str').hide();
                                $('#id_password_str').hide();
                                $('#id_client_key').hide();

                                $('#username').text(username);
                                var hidden_password = "";
                                $.each( password, function(c){
                                    hidden_password += "*";
                                });
                                $('#password').text(hidden_password);
                                $('#client_key').text(client_key);
                                $('.login-credentials-submit').hide();
                                $('.login-credentials-settings').show();
                                saved_new_login = true;
                            } else {
                                $(message).html("Invalid login information.");
                            }
                        }
                    });
            });

            $("#edit-login").click(function() {
                    $('#id_username_str').show();
                    $('#id_password_str').show();
                    $('#id_client_key').show();

                    $('#username').text('');
                    $('#password').text('');
                    $('#client_key').text('');

                    $('.login-credentials-submit').show();
                    $('.login-credentials-settings').hide();
            });

            $('.network_type_dependant').each(function() {
                    $(this).toggle($(this).hasClass(network_type));
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

            // Show location-dependent fields when location targeting is turned on
            $('#campaign_and_adgroup input[name="region_targeting"]').click(function(e) {
                var loc_targ = $(this).val();
                $('.locationDependent', '#campaign_and_adgroup').hide();
                $('.' + loc_targ + '.locationDependent', '#campaign_and_adgroup').show();
                if ($(this).val() == 'all') {
                    $('li.token-input-city span.token-input-delete-token').each(function() {
                        $(this).click();
                    });
                }
            }).filter(':checked').click();

            $('span.pub_id').click(function() {
                var pub_id = pub_ids[network_type];
                $(this).siblings('input[name$="'+pub_id+'"]').show();
                $(this).siblings('span').hide();
                $(this).hide();
            });


            $('.pub_id').hide();
            $('.cpm-span').hide();
            $('.cpm-cancel').hide();

            $('tr.sub').hover(function() {
                    $(this).find('span.pub_id').show();
                    $(this).find('span.cpm-span').show();
                }, function() {
                    $(this).find('span.pub_id').hide();
                    $(this).find('span.cpm-span').hide();
            });

            $('div.cpm-override').click(function(event) {
                event.preventDefault();
                $(this).parents('tbody').find('.cpm-input').toggle();
            });
            $('div.cpm-override').tooltip({
                title:'Set CPM for ad units'
            });


            $('td.pub-id-data').each(function () {
                var input = $(this).children('div').children('input[name$="'+pub_id+'"]');
                var value = input.val();

                if (!$(this).hasClass('adunit')) {
                    // Always show the input at the app level
                    input.show();

                }
                
                if(value) {
                    input.siblings('span.pub_id.muted').text(value);
                    input.siblings('span.pub_id').show();
                    if (!$(this).hasClass('adunit')) {
                        // Set up tooltip for arrow widget
                        input.siblings('span.pub_id.ui-icon').tooltip({
                            title:'Edit Network ID',
                            placement:'bottom'
                        });
                    }
                }
                else {
                    if (!$(this).hasClass('adunit')) {
                        // If this is the app level td, always show the input box if empty
                        //input.show();
                    }
                    else {
                        // If this is an ad unit level td, show the value of the app
                        var app_body = $(this).parents('tbody');
                        var app_input = app_body.children('tr.app-targeting').find('input[name$="'+pub_id+'"]');
                        var app_value = app_input.val();
                        //input.siblings('span.pub_id.muted').text(app_value);
                        //input.siblings('span.pub_id').show();
                    }
                }
            });

            // Set up tooltip to guide pubs to enable apps
            if (!$('input[class$=adunit]').filter(':checked').length) {
                var starting_tooltip = $('thead td.pub-id-data').tooltip({                
                    title: 'Check where to show this network',
                    trigger: 'manual',
                    placement:'top'
                });
                starting_tooltip.tooltip('show');                
            }

            /* GEO TARGETING */
            var geo_s = 'http://api.geonames.org/searchJSON?username=MoPub&';
            var pre = {type: 'country', data: []};
            var city_pre = {type: 'city', data: []};

            for (var count = 0; count < countries.length; count++) {
                var dat = countries[count];
                if ($.inArray(dat.code, priors) != -1) {
                    pre.data.push(dat);
                }
                if (pre.length == priors.length) {
                    break;
                }
            }
            //city is ll:ste:name:ccode;
            for (var i in city_priors) {
                if (city_priors.hasOwnProperty(i)) {
                    var datas = city_priors[i].split(':');
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

            // Show location-dependent fields when location targeting is turned on
            $('#campaign_and_adgroup input[name="region_targeting"]').click(function(e) {
                var loc_targ = $(this).val();
                $('.locationDependent', '#campaign_and_adgroup').hide();
                $('.' + loc_targ + '.locationDependent', '#campaign_and_adgroup').show();
                if ($(this).val() == 'all') {
                    $('li.token-input-city span.token-input-delete-token').each(function() {
                        $(this).click();
                    });
                }
            }).filter(':checked').click();

            $('#networkLoginForm-cancel').click(function () {
                $('#networkLoginForm').slideUp(400, function () {
                    $('#networkLoginForm-show').show();
                });
            });

            $('#networkLoginForm-show').click(function () {
                $('#networkLoginForm-show').hide();
                $('#networkLoginForm').slideDown();
            });
        }
    }

    var NetworkDetailsController = { 
        initialize: function(bootstrapping_data) {
            var campaign_data = bootstrapping_data.campaign_data,
                graph_start_date = bootstrapping_data.graph_start_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            initializeDateButtons();

            var all_campaigns = initialize_campaign_data(campaign_data, true, ajax_query_string);

            // create campaigns collection
            campaigns = new Campaigns(all_campaigns);

            var graph_view = new NetworkGraphView({
                collection: campaigns,
                today: today,
                yesterday: yesterday,
                start_date: graph_start_date,
                line_graph: true,
                mopub_optimized: false,
            });

            initialize_show_network();

            $('#network-settingsButton')
                .button({ icons: { primary: "ui-icon-wrench" } })

            $('#delete-network')
                .click(function () {
                    var key = $(this).attr('id');
                    var div = $('.' + key);
                    div.dialog({
                        buttons: {
                            "Delete": function() {
                                $.post('/networks/delete',
                                    {campaign_key: campaign_data.id},
                                    function() {
                                      window.location = '/networks';
                                });
                                },
                            "Cancel": function() { $(this).dialog('close');} }
                    });
                });

            $('#network-editActive').change(function () {
                var hidden_li = $('#network-editActive-menu').find('li:hidden');
                var shown_li = $('#network-editActive-menu').find('li:not(:hidden)');
                hidden_li.show();
                shown_li.hide();

                $.post('/networks/pause', { campaign_key: campaign_data.id,
                                             active: $(this).val() } );
            });

            $('#network-editActive-menu').find('li').first().hide();

            }
    }

    window.NetworkDetailsController = NetworkDetailsController;
    window.NetworksController = NetworksController;
    window.EditNetworkController = EditNetworkController;
});

