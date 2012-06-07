(function($, _) {

    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    function initialize_campaign_data(campaign_data, apps, include_adunits) {
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

            campaign.fetch({
                error: function() {
                    campaign.fetch({
                        error: toast_error
                    });
                }
            });
        });

        var network_apps = [];
        _.each(all_campaigns, function(campaign) {
            _.each(apps, function(app) {
                var network_app = new App({id: app.id,
                                           campaign_id: campaign.id,
                                           stats_endpoint: campaign.get('stats_endpoint')});

                var app_view = new AppView({model: network_app,
                             endpoint_specific: true,
                             network: campaign.get('network')});
                app_view.el = '.' + campaign.id + '-apps-div';

                network_apps.push(network_app);
            });
        });

        if(include_adunits) {
            var adunits = new AdUnitCollection();
            adunits.campaign_id = mopub_campaign.id;
            adunits.stats_endpoint = mopub_campaign.get('stats_endpoint');

            new AdUnitCollectionView({collection: adunits,
                                      campaign: mopub_campaign});

            return [all_campaigns, network_apps, adunits];
        } else {
            return [all_campaigns, network_apps];
        }
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
                apps = bootstrapping_data.apps,
                date_range = bootstrapping_data.date_range,
                graph_start_date = bootstrapping_data.graph_start_date;

            // TODO: move fuction to mopub.js
            initializeDateButtons();

            var all_campaigns = [];
            var apps_by_campaign = {};
            _.each(campaigns_data, function(campaign_data) {
                var result = initialize_campaign_data(campaign_data, apps, false);
                all_campaigns = all_campaigns.concat(result[0]);
                network_apps = apps_by_campaign[result[0][0].id] = result[1];
            });

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
                // load the apps via ajax
                _.each(apps_by_campaign[key], function(network_app) {
                    network_app.fetch({
                        error: function() {
                            network_app.fetch({
                                error: toast_error
                            });
                        },
                    });
                });
            });

            var campaigns = new Campaigns(all_campaigns);

            // Load chart
            new NetworkGraphView({
                collection: campaigns,
                date_range: date_range,
                start_date: graph_start_date,
                line_graph: false,
                mopub_optimized: false,
            });

            new NetworkDailyCountsView({collection: campaigns});

            initialize_show_network();

            $('.appData').hover(
                function() {
                    $(this).find('.edit-link').show()
                },
                function() {
                    $(this).find('.edit-link').hide()
                }
            );

            $('#network-editSelect').change(function() {
                if ($(this).val()) {
                    window.location = $(this).val();
                }
                $(this).selectmenu('index', 0);
            });

            $('#network-editSelect-menu').find('li').first().hide();

            // TODO: move to a utils package
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

            $('.dailyCount-toggleButton')
                .button('option', {icons: { primary: 'ui-icon-triangle-1-s' }})
                .click(function(e) {
                    e.preventDefault();
                    if ($('#dailyCounts-individual').is(':hidden')) {
                        $('#dailyCounts-individual').slideDown('fast');
                        $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
                    } else {
                        $('#dailyCounts-individual').slideUp('fast');
                        $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
                    }
                });

        }
    }

    var EditNetworkController = {
        initialize: function(bootstrapping_data) {
            var network_type = bootstrapping_data.network_type,
                pretty_name = bootstrapping_data.pretty_name,
                adunits_for_app = bootstrapping_data.adunits_for_app,
                app_for_adunit = bootstrapping_data.app_for_adunit,
                account_key = bootstrapping_data.account_key,
                priors = bootstrapping_data.priors,
                city_priors = bootstrapping_data.city_priors,
                login_state = bootstrapping_data.login_state,
                LoginStates = bootstrapping_data.LoginStates;
            
            var saved_new_login = false;

            // set up tabIndex attributes for vertical tabbing
            var rows = $('table.inventory_table').children().not('thead').find('tr');
            rows.each(function(row_iter, row) {
                $(row).find('td').each(function(data_iter, data) {
                    $(data).find('input, textarea').attr('tabIndex', rows.length * data_iter + row_iter);
                });
            });

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

            $('#campaignForm-keyword-helpLink').click(function(e) {
                e.preventDefault();
                $('#campaignForm-keyword-helpContent').dialog({
                    buttons: { "Close": function() { $(this).dialog("close"); } }
                });
            });
            $('#campaignForm-customHtml-helpLink').click(function(e) {
                e.preventDefault();
                $('#campaignForm-customHtml-helpContent').dialog({
                    buttons: { "Close": function() { $(this).dialog("close"); }},
                    width: 700
                });
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

            // text entered for app level network ids should propogate to
            // children
            $('.app-pub-id')
                .keyup(function () {
                    var value = $(this).val();
                    var tbody = $(this).closest('tbody');
                    $(tbody).children().not('tr.main').find('input[name$="'+pub_id+'"]').each(function () {
                        if (!$(this).hasClass('initialized')) {
                            $(this).val(value);
                            var pub_id_value = value;
                            if (!value) {
                                pub_id_value = "Change Network ID";
                            }
                            $(this).closest('td').find('.pub-id-edit').text(pub_id_value);
                        }
                    });
                }).keyup();

            // perculate checked change up to global
            function update_global_active() {
                if($('.app-active').length == $('.app-active:checked').length) {
                    $('.global-active').attr("checked", "checked");
                } else {
                    $('.global-active').removeAttr("checked");
                }
            }

            // global enabled checkbox
            $('.global-active')
                .change(function() {
                    if($('.global-active').is(':checked')) {
                        $('.app-active').attr('checked', 'checked');
                        $('input[name$="active"]').attr('checked', 'checked');
                    } else {
                        $('.app-active').removeAttr("checked");
                        $('input[name$="active"]').removeAttr("checked");
                    }
                });

            // set up active checkbox's for app level
            $('.app-active')
                .change(function() {
                    var checkboxes = $(this).closest('tbody').find('input[name$="active"]');
                    if ($(this).is(':checked')) {
                        checkboxes.attr("checked", "checked");
                    } else {
                        checkboxes.removeAttr("checked");
                    }

                    update_global_active();
                });

            // perculate checked changes up
            $('input[name$="active"]')
                .change(function () {
                    var tbody = $(this).closest('tbody'); 
                    var key = $(this).attr('class');
                    if(tbody.find('input[name$="active"]:checked').length == tbody.find('input[name$="active"]').length) {
                        tbody.find('.app-active').attr("checked", "checked");
                    } else {
                        tbody.find('.app-active').removeAttr("checked");
                    }

                    update_global_active();

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

            // set cpms when copy all cpm button is clicked for either 14 day
            // or 7 day
            _.each(['7-day', '14-day'], function(days) {
                // copy over cpms for all apps
                $('#copy-' + days).click(function() {
                    $('.inventory_table tbody').each(function() {
                        // if global cpm is open close it
                        if(!$('.global-cpm-input').is(':hidden')) {
                            $('.global-cpm-input').hide();
                            $('.global-cpm-close').show();

                            $('.app-cpm-input').show();
                            $('.app-cpm-close').hide();
                        }

                        var cpm = parseFloat($(this).find('.copy-' + days).text().replace('$', '')).toString();
                        var input = $(this).find('.app-cpm-input input');
                        // change app level cpm
                        input.val(cpm);
                        // change adunit level cpm
                        $(this).find('.cpm-input input').val(cpm);
                        });
                    });
                // copy over an individual app level cpm
                $('.copy-' + days).click(function() {
                    // if global cpm is open close it
                    if(!$('.global-cpm-input').is(':hidden')) {
                        $('.global-cpm-input').hide();
                        $('.global-cpm-close').show();

                        $('.app-cpm-input').show();
                        $('.app-cpm-close').hide();
                    }

                    var cpm = parseFloat($(this).parent().text().replace('$', '')).toString();
                    var tbody = $(this).closest('tbody')
                    var input = tbody.find('.app-cpm-input input');
                    // change app level cpm
                    input.val(cpm);
                    input.keyup();
                    // change adunit level cpm
                    tbody.find('.cpm-input input').val(cpm);
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
            // select the appropriate campaign_type from the hash
            if (window.location.hash.substring(1) !== '') {
                $('select[name="campaign_type"]').val(window.location.hash.substring(1));
            }

            var validator = $('form#campaign_and_adgroup').validate({
                errorPlacement: function(error, element) {
                    element.parents('div').not(':hidden').first().append(error);
                },
                submitHandler: function(form) {
                    $(form).ajaxSubmit({
                        data: {ajax: true},
                        dataType: 'json',
                        success: function(jsonData, statusText, xhr, $form) {
                            $('#loading').hide();
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
                            $('#loading').hide();
                            $('form#campaign_and_adgroup #submit').button({
                                label: 'Try Again',
                                disabled: false
                            });
                        },
                        beforeSubmit: function(arr, $form, options) {
                            $('#loading').css('display', 'inline');
                            $('form#campaign_and_adgroup #submit').button({label: 'Submitting...',
                                                                           disabled: true});
                        }
                    });
                }
            });

            $('form#campaign_and_adgroup #submit')
                .button({ icons : { secondary : 'ui-icon-circle-triangle-e' } })
                .click(function(e) {
                    e.preventDefault();
                    $('form#campaign_and_adgroup').submit();
                });

            function setupLoginForm() {
                $('form#network-login-form .submit, form#campaign_and_adgroup .submit').click(function() {
                        if ($(this).closest('form').attr('id') == 'network-login-form') {
                            var data = $(this).closest('form').serialize();
                        } else {
                            // Hack to serialize sub-section of forms data.
                            // Add a new form and hide it.
                            $('#campaign_and_adgroup').append('<form id="form-to-submit" style="visibility:hidden;"></form>');
                            // Clone the fieldset into the new form.
                            $('#form-to-submit').html($(this).closest('.login-fields').clone());
                            // Serialize the data.
                            var data = $('#form-to-submit').serialize();
                            // Remove the form.
                            $('#form-to-submit').remove();
                        }
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
                                    $(message).html("MoPub is currently pulling data from "
                                                    + pretty_name + " using the following credentials.");
                                    var username = $('#id_' + network_type + '-username_str').val();
                                    var password = $('#id_' + network_type + '-password_str').val();
                                    var client_key = $('#id_' + network_type + '-client_key').val();

                                    $('#id_' + network_type + '-username_str').hide();
                                    $('#id_' + network_type + '-password_str').hide();
                                    $('#id_' + network_type + '-client_key').hide();

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
                            },
                        });
                });

                $('form#network-login-form .cancel').click(function () {
                    $('#network-settingsForm').slideUp();
                });
            }

            setupLoginForm();

            $('form#campaign_and_adgroup .cancel').click(function () {
                var fieldset = $(this).closest('.login-fields');

                $(this).removeClass('ui-state-hover');
                $('#network-login-form').html(fieldset.clone());

                // rebuild buttons
                // TODO: remove terrible designer buttons so hacks like this
                // aren't needed
                $('form#network-login-form .button').addClass('button-small');
                $('form#network-login-form .button').button();

                fieldset.slideUp(400, function () {
                    fieldset.remove();
                    $('#title-bar-button').show();
                });

                // re-initialize event handlers for the moved form
                setupLoginForm();
            });


            $("#edit-login").click(function() {
                $('#id_' + network_type + '-username_str').show();
                $('#id_' + network_type + '-password_str').show();
                $('#id_' + network_type + '-client_key').show();

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

            $('td.pub-id-data').each(function () {
                var input = $(this).children('div').children('input[name$="'+pub_id+'"]');
                var value = input.val();

                // TODO: review
                // Always show the app-level input
                if (value || !$(this).hasClass('adunit')) {
                    input.show();
                    input.parents('td').find('.pub-id-edit').hide();
                }                
            });

            // Click the ad unit placeholder text to edit
            $('.pub-id-edit').click(function (event) {
                event.preventDefault();
                $(this).hide();
                var div = $(this).siblings('.pub-id-input')
                div.show();
                div.find('input').addClass('initialized');
            });
            $('.pub-id-edit').tooltip({
                title: "Set ID for this ad unit"
            });
            $('.cpm-edit').tooltip({
                title: "Set CPM for each unit"
            });            
            $('.app-cpm-close').tooltip({
                title: "Set CPM at the app level"
            });                        

            $('.pub-id-close').click(function (event) {
                event.preventDefault;
                var input_div = $(this).closest('.pub-id-input');
                input_div.hide();

                var value = input_div.children('input').val()
                if (value) {
                    $(this).closest('td').find('.pub-id-edit').text(value);
                } else {
                    $(this).closest('td').find('.pub-id-edit').text("Change Network ID");
                }
                $(this).closest('td').find('.pub-id-edit').show();
            });


            /* Setting cpm, custom_html and custom_native */
            var fields = [['cpm', 'input']]
            if(network_type == 'custom') {
                fields.push(['custom_html', 'textarea']);
            } else if(network_type == 'custom_native') {
                fields.push(['custom_method', 'input']);
            }

            _.each(fields, function(field_props) {
                var field = field_props[0];
                var type = field_props[1];

                // adunit level
                $('.' + field + '-input ' + type).keyup(function() {
                    var value = $(this).val();
                    var td = $(this).closest('td');
                    $(td).find('.' + field + '-value').text(value);
                }).keyup();

                $('.' + field + '-edit').click(function (event) {
                    if(!$('.global-' + field + '-input').is(':hidden')) {
                        $('.global-' + field + '-input').hide();
                        $('.global-' + field + '-close').show();

                        $('.app-' + field + '-input').show();
                        $('.app-' + field + '-close').hide();

                        // show app level fields
                        $('.app-' + field + '-input').show();
                        // hide app edit text
                        $('.app-' + field + '-close').hide();
                    }
                    event.preventDefault();
                    var tbody = $(this).closest('tbody');
                    // hide app level fields
                    tbody.find('.app-' + field + '-input').hide();
                    tbody.find('.app-' + field + '-close').show();
                    tbody.find('.app-' + field + '-close').text("Set app " + field.replace('_', ' '));
                    // show adunit level fields
                    tbody.find('.' + field + '-edit').hide();
                    tbody.find('.' + field + '-input').show();
                });

                // app level
                $('.app-' + field + '-input ' + type).keyup(function() {
                    var value = $(this).val();
                    var tbody = $(this).closest('tbody');
                    $(tbody).find('.' + field + '-input ' + type).val(value);
                    if(!value) {
                        value = "Set adunit " + field.replace('_', ' ');
                    }
                    $(tbody).find('.' + field + '-value').text(value);
                });

                $('.app-' + field + '-close').click(function (event) {
                    event.preventDefault;
                    if($('.global-' + field + '-input').is(':hidden')) {
                        elements = $(this);
                    } else {
                        $('.global-' + field + '-input').hide();
                        $('.global-' + field + '-close').show();

                        $('.app-' + field + '-input').show();
                        $('.app-' + field + '-close').hide();

                        elements = $('.app-' + field + '-close');
                    }

                    elements.each(function() {
                        var tbody = $(this).closest('tbody');
                        // copy value of first adunit input to all fields inputs
                        var value = tbody.find('.' + field + '-input ' + type).val();
                        tbody.find('.' + field + '-input ' + type).val(value);
                        tbody.find('.app-' + field + '-input ' + type).val(value);

                        if(!value) {
                            value = "Set adunit " + field.replace('_', ' ');
                        }
                        tbody.find('.' + field + '-value').text(value);

                        // show app level fields
                        tbody.find('.app-' + field + '-input').show();
                        // hide app edit text
                        tbody.find('.app-' + field + '-close').hide();

                        // hide adunit fields for app
                        tbody.find('.' + field + '-input').hide();
                        // show adunit edit text
                        tbody.find('.' + field + '-edit').show();
                    });
                });

                // global level
                $('.global-' + field + '-input ' + type).keyup(function() {
                    var value = $(this).val();
                    $('.' + field + '-value').text(value);
                    $('.' + field + '-input ' + type).val(value);
                    $('.app-' + field + '-input ' + type).val(value);

                    if(!value) {
                        $('.' + field + '-value').text("Set adunit " + field.replace('_', ' '));
                        value = "Set app " + field.replace('_', ' ');
                    }
                    $('.app-' + field + '-close').text(value);
                });

                $('.global-' + field + '-close').click(function (event) {
                    event.preventDefault;
                    // copy value of first adunit to all field inputs
                    var value = $('.' + field + '-input ' + type).val();
                    $('.global-' + field + '-input ' + type).val(value);
                    $('.' + field + '-value').text(value);
                    $('.' + field + '-input ' + type).val(value);
                    $('.app-' + field + '-input ' + type).val(value);

                    if(!value) {
                        $('.' + field + '-value').text("Set adunit " + field.replace('_', ' '));
                        value = "Set app " + field.replace('_', ' ');
                    }
                    $('.app-' + field + '-close').text(value);

                    // show global field
                    $('.global-' + field + '-input').show();
                    // hide global edit text
                    $('.global-' + field + '-close').hide();

                    // hide adunit fields for app
                    $('.' + field + '-input').hide();
                    // hide app fields for app
                    $('.app-' + field + '-input').hide();
                    // show adunit edit text
                    $('.' + field + '-edit').show();
                    // show app edit text
                    $('.app-' + field + '-close').show();
                });
            });

            // Initialize active
            $('input[name$="active"]').change();


            /* Initialize cpm, custom_html and custom_native */
            _.each(fields, function(field_props) {
                var field = field_props[0];
                var type = field_props[1];

                var all_apps_equal = true;
                var global_value = $('.adunit-row .' + field + '-input ' + type).val();
                $('.app-tbody').each(function() {
                    var all_adunits_equal = true;
                    var value = $(this).find('.adunit-row .' + field + '-input ' + type).val();
                    // check if all adunits have the same value for the field
                    $(this).find('.adunit-row .' + field + '-input ' + type).each(function() {
                        if(value != $(this).val()) {
                            all_adunits_equal = false;
                        }
                    });

                    if(all_adunits_equal) {
                        if(global_value != value) {
                            all_apps_equal = false;
                        }

                        $(this).find('.adunit-row .' + field + '-input').hide();
                        $(this).find('.adunit-row .' + field + '-edit').show();

                        $(this).find('.app-' + field + '-input ' + type).val(value);
                        $(this).find('.app-' + field + '-input').show();
                        $(this).find('.app-' + field + '-close').hide();
                    } else {
                        all_apps_equal = false;
                    }
                });

                if(all_apps_equal) {
                    var value = $('.app-' + field + '-input ' + type).val();

                    $('.app-' + field + '-input').hide();
                    $('.app-' + field + '-close').show();

                    $('.global-' + field + '-close').hide();
                    $('.global-' + field + '-input ' + type).val(value);
                    $('.global-' + field + '-input').show();

                    if(!value) {
                        $('.' + field + '-value').text("Set adunit " + field.replace('_', ' '));
                        value = "Set app " + field.replace('_', ' ');
                    }
                    $('.app-' + field + '-close').text(value);
                }
            });

            var MODAL_FIELDS = ([['allocation_percentage', '%, '], ['daily_frequency_cap', '/d '],
                ['hourly_frequency_cap', '/h']]);
            var ALL_KEYS = _.keys(app_for_adunit).concat(_.keys(adunits_for_app)).concat(['global']);
            function check_global(text, global_values) {
                // text and global_values are candidates for global values
                var all_equal = true;
                // check if all apps are the same
                _.each(_.keys(adunits_for_app), function(app_key) {
                    if(text != $('#' + app_key + '-options-edit').text()) {
                        all_equal = false;
                    }
                });

                var global_text = '';
                if(!all_equal || text == 'Set app options') {
                    global_text = 'Set global options';
                    global_values = ['','',''];
                } else {
                    global_text = text;
                }
                
                $('#global-options-edit').text(global_text);
                // Clear global fields
                _.each(_.zip(MODAL_FIELDS, global_values), function(field) {
                    var field_name = field[0][0];
                    var value = field[1];
                    $('#id_global-' + field_name).val(value);
                });
            }

            /* Advanced Options Modal */
            function modal_ok(row, modal_div) {
                var key = row.attr('id').replace('-row', '');
                var app_div = $(modal_div).parent();

                var values = [];
                var text = '';
                _.each(MODAL_FIELDS, function(field) {
                    var field_name = field[0];
                    var field_term = field[1];
                    var value = $('#id_' + key + '-' + field_name).val();
                    values.push(value);
                    if(value != undefined && value != '' &&
                            (field_name.indexOf("_frequency_cap") == -1 || value != '0') &&
                            (field_name.indexOf("_percentage") == -1 || value != '100.0')) {
                        text += value + field_term;
                    }
                });
                if(!text) {
                    text = "None"
                }

                if($(row).hasClass('adunit-row')) {
                    app_key = app_for_adunit[key];
                    // adunit level
                    $('#' + key + '-options-edit').text(text);

                    var all_equal = true;
                    _.each(adunits_for_app[app_key], function(adunit_key) {
                        if(text != $('#' + adunit_key + '-options-edit').text()) {
                            all_equal = false;
                        }
                    });

                    if(all_equal) {
                        var app_text = text;
                        var app_values = values;
                    } else {
                        var app_text = 'Set app options';
                        var app_values = ['','',''];
                    }

                    // perculate to app level
                    $('#' + app_key + '-options-edit').text(app_text);
                    // Clear app fields
                    _.each(_.zip(MODAL_FIELDS, app_values), function(field) {
                        var field_name = field[0][0];
                        var value = field[1];
                        $(app_div).find('#id_' + app_key + '-' + field_name).val(value);
                    });

                    // perculate to global level
                    check_global(app_text, app_values);
                } else if($(row).hasClass('app-row')) {
                    // app level
                    _.each(adunits_for_app[key].concat(key), function(key) {
                        $('#' + key + '-options-edit').text(text);

                        // update all adunit fields
                        _.each(_.zip(MODAL_FIELDS, values), function(field) {
                            var field_name = field[0][0];
                            var value = field[1];
                            $('#id_' + key + '-' + field_name).val(value);
                        });
                    });

                    // perculate to global level
                    check_global(text, values);

                } else {
                    // global level
                    var selector = $(modal_div).parent().parent();
                    _.each(ALL_KEYS, function(key) {
                        $('#' + key + '-options-edit').text(text);

                        // update all fields
                        _.each(_.zip(MODAL_FIELDS, values), function(field) {
                            var field_name = field[0][0];
                            var value = field[1];
                            $('#id_' + key + '-' + field_name).val(value);
                        });
                    });
                }
            }

            // open advanced options modal for global app or adunit
            _.each(ALL_KEYS, function(key) {
                $('#' + key + '-options-edit').click(function() {
                    var row = $('#' + key + '-row');
                    var modal_div = $('#' + key + '-options');
                    // open the correct modal
                    $(modal_div).show();
                    $(modal_div).modal('show');

                    $(modal_div).find('.save').click(function() { 
                        modal_ok(row, modal_div);
                        $(modal_div).modal('hide');
                    });

                    $(modal_div).find('.close').click(function() {
                        $(modal_div).modal('hide');
                    });
                });
            });

            /* Initialize advanced options and active fields */
            // mimic an entry for each adunit to prepopulate settings
            // at app and global levels
            _.each(_.flatten(_.values(adunits_for_app)), function(adunit_key) {
                adunit_row = $('#' + adunit_key + '-row')

                // prepopulate advanced options modals
                var modal_div = $('#' + adunit_key +'-options');
                modal_ok(adunit_row, modal_div);
            });

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

        }
    }

    var NetworkDetailsController = { 
        initialize: function(bootstrapping_data) {
            var campaign_data = bootstrapping_data.campaign_data,
                apps = bootstrapping_data.apps,
                graph_start_date = bootstrapping_data.graph_start_date;

            initializeDateButtons();

            var result = initialize_campaign_data(campaign_data, apps, true);
            var all_campaigns = result[0];
            var network_apps = result[1];
            var adunits = result[2];


            _.each(network_apps, function(network_app) {
                network_app.fetch({
                    error: function() {
                        network_app.fetch({
                            error: toast_error
                        });
                    },
                });
            });

            adunits.fetch({
                error: function() {
                    adunits.fetch({
                        error: toast_error
                    });
                },
            });

            // create campaigns collection
            campaigns = new Campaigns(all_campaigns);

            new NetworkGraphView({
                collection: campaigns,
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

})(this.jQuery, this._);

