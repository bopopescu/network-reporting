(function($, _) {

    /*
     * ## App
     * We might consider turning derivative values (cpm, fill_rate, ctr) into
     * functions.
     */
    var App = StatsModel.extend({
        defaults : {
            name: '',
            url:'#',
            icon_url: "/placeholders/image.gif",
            app_type: '',
            active: false,
            att: 0,
            clk: 0,
            ctr: 0,
            cpm: 0,
            fill_rate: 0,
            imp: 0,
            price_floor: 0,
            requests: 0,
            rev: 0,
            status: 'Running',
            stats_endpoint: 'all'
        },
        url: function () {
            var stats_endpoint = this.get('stats_endpoint');
            if (this.get('campaign_id')) {
                return '/api/campaign/'
                    + this.get('campaign_id')
                    + '/apps/'
                    + this.id
                    + "?"
                    + window.location.search.substring(1)
                    + '&endpoint='
                    + stats_endpoint;
            } else {
                return '/api/app/'
                    + this.id
                    + "?"
                    + window.location.search.substring(1)
                    + '&endpoint='
                    + stats_endpoint;
            }
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            var app = response[0];

            // REFACTOR attempts vs requests
            if(app.req == null || app.req == undefined) {
                app.req = app.att;
            } else if (app.att == null || app.att == undefined) {
                app.att = app.req;
            }

            if (app.app_type === 'iphone') {
                app.app_type = 'iOS';
            }
            if (app.app_type === 'android') {
                app.app_type = 'Android';
            }
            if (app.app_type === 'mweb') {
                app.app_type = 'Mobile Web';
            }
            return app;
        },
        get_summed: function (attr) {
            if (typeof(this.get(attr)) !== 'undefined') {
                var series = this.get(attr);
                var sum = _.reduce(series, function(memo, num){
                    return memo + num;
                }, 0);
                return sum;
            }
            return null;
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
            if (this.options.endpoint_specific) {
                this.model.bind('change', this.render, this);
            }
            try {
                this.template = _.template($('#app-template').html());
            } catch (e) {
                // the template wasn't specified. this is ok if you
                // intend to renderInline
            }
        },

        renderInline: function () {
            var this_view = this;
            // Will there be multiple stats endpoints in this app row?
            if (this_view.options.endpoint_specific) {
                if (this_view.model.get('stats_endpoint') == 'networks') {
                    var selector = ' .network-data';
                } else {
                    var selector = ' .mopub-data';
                }
            } else {
                var selector = ''
            }
            var app_row = $('tr.app-row#app-' + this_view.model.id, this_view.el);

            /*jslint maxlen: 200 */
            if (!this_view.options.endpoint_specific || this_view.model.get('stats_endpoint') == 'networks') {
                $('.rev', app_row).text(this_view.model.get_formatted_stat('rev'));
                $('.cpm', app_row).text(this_view.model.get_formatted_stat('cpm'));
            }
            var metrics = ['imp', 'clk', 'ctr', 'fill_rate', 'req', 'att', 'conv', 'conv_rate'];
            _.each(metrics, function (metric) {
                if (this_view.model.get('stats_endpoint') != 'networks'
                        || this_view.options.network != 'mobfox' || (metric != 'att'
                        && metric != 'fill_rate')) {
                    $('.' + metric + selector, app_row).text(this_view.model.get_formatted_stat(metric));
                }
            });
            /*jslint maxlen: 110 */

            $(".loading-img", app_row).hide();

            return this;
        },
        render: function () {
            if(!this.template) {
                return this.renderInline();
            }

            var renderedContent = $(this.template(this.model.toJSON()));

            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            $('tbody', this.el).append(renderedContent);
            return this;
        }
    });


    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    function hashDiff(h1, h2) {
        var d = {};
        for (k in h2) {
            if (h1[k] !== h2[k]) d[k] = h2[k];
        }
        return d;
    }
    // TODO: move to a utils package
    // checks if email is valid
    function isValidEmailAddress(emailAddress) {
        var pattern = new RegExp(/^(\s*)(("[\w-+\s]+")|([\w-+]+(?:\.[\w-+]+)*)|("[\w-+\s]+")([\w-+]+(?:\.[\w-+]+)*))(@((?:[\w-+]+\.)*\w[\w-+]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$)|(@\[?((25[0-5]\.|2[0-4][\d]\.|1[\d]{2}\.|[\d]{1,2}\.))((25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\.){2}(25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\]?$)/i);
        return pattern.test(emailAddress);
    };


    function convertSerializedArrayToHash(a) {
        var r = {};
        for (var i = 0; i < a.length; i++) {
            // if the name is already in the dict append the value to a list
            if(a[i].name in r) {
                if(typeof a[i].value == 'string') {
                    // if the value is a string
                    r[a[i].name] = [r[a[i].name], a[i].value];
                } else {
                    // if the value is a list
                    r[a[i].name].append(value);
                }
            } else {
                r[a[i].name] = a[i].value;
            }

        }
        return r;
    }

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

        // Create NetworkView and fetch mopub campaign and network
        // campaign if campaign has reporting
        _.each(all_campaigns, function(campaign) {

            new NetworkView({
                model: campaign
            });

            campaign.fetch({
                error: function() {
                    campaign.fetch({
                        error: toast_error
                    });
                },
                success: function () {

                }
            });
        });

        var network_apps = [];
        _.each(all_campaigns, function(campaign) {
            _.each(apps, function(app) {
                var network_app = new App({
                    id: app.id,
                    campaign_id: campaign.id,
                    stats_endpoint: campaign.get('stats_endpoint')
                });

                var app_view = new AppView({
                    model: network_app,
                    endpoint_specific: true,
                    network: campaign.get('network')
                });
                app_view.el = '.' + campaign.id + '-apps-div';

                network_apps.push(network_app);
            });
        });

        if (include_adunits) {
            var adunits = new AdUnitCollection();
            adunits.campaign_id = mopub_campaign.id;
            adunits.stats_endpoint = mopub_campaign.get('stats_endpoint');

            new AdUnitCollectionView({
                collection: adunits,
                campaign: mopub_campaign
            });

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
                hide_network_trafficChart_series();
            }
        });

        // We drop a cookie when someone clicks on the 'show reporting data'
        // check box, so that their preference is saved. If that cookie exists,
        // check the box automatically.
        if (!$.cookie("show-network-data")) {
            $('#show-network').click();
        } else {
            $('#show-network').change();
        }
    };

    var NetworksController = {

        initialize: function(bootstrapping_data) {

            // Set up variables from the boostrapping data
            var campaigns_data = bootstrapping_data.campaigns_data,
                apps = bootstrapping_data.apps,
                date_range = bootstrapping_data.date_range,
                graph_start_date = bootstrapping_data.graph_start_date;

            // Initialize common stuff
            // TODO: move fuction to mopub.js
            initializeDateButtons();

            // Make the new network selector really fancy
            function network_option_format(network) {
                console.log(network);
                return "<img src='/images/" + network.id.toLowerCase()  + "-transparent.png'/>" + network.text;
            }


            $("#network-editSelect").chosen().bind("change", function() {
                window.location = $(this).val();
            });


            // Fetch all the campaign data and render each network as a table row
            var all_campaigns = [];
            var apps_by_campaign = {};
            _.each(campaigns_data, function(campaign_data) {

                var result = initialize_campaign_data(campaign_data, apps, false);
                all_campaigns = all_campaigns.concat(result[0]);
                var network_apps = apps_by_campaign[result[0][0].id] = result[1];
            });

            // Set up the click handler that shows the apps targeted
            // by each network
            $('.show-apps').click(function() {
                var key = $(this).attr('id');
                var div = $('.' + key + '-apps-div');
                if (div.is(':hidden')) {
                    div.show();
                    $(this).children('span').text("Hide Apps");
                } else {
                    div.hide();
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
                mopub_optimized: false
            });

            new NetworkDailyCountsView({
                collection: campaigns
            });

            initialize_show_network();

            $('.appData').hover(
                function() {
                    $(this).find('.edit-link').show();
                },
                function() {
                    $(this).find('.edit-link').hide();
                }
            );



            // taken from mopub-dashboard.js #appEditForm (could be combined)
            $('#networkSettingsForm-submit')
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
                .click(function(e) {
                    e.preventDefault();
                    if ($('#network-settingsForm').is(':visible')) {
                        $('#network-settingsForm').slideUp('fast');
                    } else {
                        $('#network-settingsForm').slideDown('fast');
                    }
                });

            $('.dailyCount-toggleButton')
                .click(function(e) {
                    e.preventDefault();
                    if ($('#dailyCounts-individual').is(':hidden')) {
                        $('#dailyCounts-individual').slideDown('fast');
                    } else {
                        $('#dailyCounts-individual').slideUp('fast');
                    }
                });

        }
    }

    var EditNetworkController = {
        initialize: function(bootstrapping_data) {
            var network_type = bootstrapping_data.network_type,
                campaign_key = bootstrapping_data.campaign_key,
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
                    var tbody = $(this).closest('tbody');
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
                .click(function() {
                    if ($('.advanced').is(':hidden')) {
                        $('.advanced').slideDown();
                        $('#advanced').html('<i class="icon-eye-close"></i>Hide Advanced Settings');
                    } else {
                        $('.advanced').slideUp();
                        $('#advanced').html('<i class="icon-eye-open"></i>Show Advanced Settings');
                    }
                });

            // TODO: merge this with controllers/campaigns.js form
            // select the appropriate campaign_type from the hash
            if (window.location.hash.substring(1) !== '') {
                $('select[name="campaign_type"]').val(window.location.hash.substring(1));
            }

            var validator = $('form#campaign_and_adgroup').validate({
                errorPlacement: function(error, element) {
                    div = element.parents('div').not(':hidden').first()
                    $(div).append(error);
                    if(error.attr('for').indexOf('pub_id') > -1) {
                        $(div).find('.pub-id-edit').click();
                    }
                },
                submitHandler: function(form) {
                    // Submit only the fields that have changed using ajaxSubmit
                    $(form).ajaxSubmit({
                        data: {ajax: true},
                        dataType: 'json',
                        success: function(jsonData, statusText, xhr, $form) {
                            $('#loading').hide();
                            if(jsonData.success) {
                                if (saved_new_login && login_state == LoginStates.NOT_SETUP) {
                                    var data = "&account_key=" + account_key + "&network=" + network_type + '&req_type=pull';

                                    $.ajax({url: 'https://checklogincredentials.mopub.com',
                                        data: data,
                                        crossDomain: true,
                                        dataType: "jsonp",
                                    });
                                }
                                window.location = jsonData.redirect;
                                $('form#campaign_and_adgroup #submit').text('Success...');
                                $('form#campaign_and_adgroup #submit').attr('disabled', 'disabled');
                            } else {
                                console.log(jsonData.errors);
                                validator.showErrors(jsonData.errors);
                                $('form#campaign_and_adgroup #submit').text('Try Again');
                                $('form#campaign_and_adgroup #submit').removeAttr('disabled');
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            $('#loading').hide();
                            $('form#campaign_and_adgroup #submit').text('Try Again');
                                $('form#campaign_and_adgroup #submit').removeAttr('disabled');
                        },
                        beforeSubmit: function(arr, $form, options) {
                            if(campaign_key) {
                                var currentItems = convertSerializedArrayToHash($form.serializeArray());
                                var itemsToSubmit = hashDiff(startItems, currentItems);
                                var extraItems = hashDiff(currentItems, startItems);

                                // hack to submit all geo/connectivity targeting
                                // if any of it changes.
                                if('accept_targeted_locations' in itemsToSubmit ||
                                   'targeted_countries' in itemsToSubmit ||
                                   'region_targeting_type' in itemsToSubmit ||
                                   'targeted_cities' in itemsToSubmit ||
                                   'targeted_regions' in itemsToSubmit ||
                                   'targeted_zip_codes' in itemsToSubmit ||
                                   'connectivity_targeting_type' in itemsToSubmit ||
                                   'targeted_carriers' in itemsToSubmit) {
                                    itemsToSubmit.accept_targeted_locations = null;
                                    itemsToSubmit.targeted_countries = null;
                                    itemsToSubmit.region_targeting_type = null;
                                    itemsToSubmit.targeted_cities = null;
                                    itemsToSubmit.targeted_regions = null;
                                    itemsToSubmit.targeted_zip_codes = null;
                                    itemsToSubmit.connectivity_targeting_type = null;
                                    itemsToSubmit.targeted_carriers = null;
                                }

                                // hack to remove items at arr location prior to
                                // submit
                                var k = 0;
                                for(i=0; i < arr.length; i++) {
                                    if(!(arr[i].name in itemsToSubmit)) {
                                        arr.splice(k, 1);
                                        i--;
                                    } else {
                                        k++;
                                    }
                                }

                                // hack for making adgroups in-active
                                for (k in extraItems) {
                                    var value = extraItems[k];
                                    if(k.indexOf('active') != -1 || k.indexOf('target_') != -1) {
                                        arr.push({'name': k,
                                                  'value': ''});
                                    }
                                }

                            }

                            $('#loading').css('display', 'inline');
                            $('form#campaign_and_adgroup #submit').text('Submitting...');
                            $('form#campaign_and_adgroup #submit').attr('disabled', 'disabled');
                        }
                    });
                }
            });

            $('form#campaign_and_adgroup #submit')
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
                var div = $(this).siblings('.pub-id-input');
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

                var value = input_div.children('input').val();
                if (value) {
                    $(this).closest('td').find('.pub-id-edit').text(value);
                } else {
                    $(this).closest('td').find('.pub-id-edit').text("Change Network ID");
                }
                $(this).closest('td').find('.pub-id-edit').show();
            });


            /* Setting cpm, custom_html and custom_native */
            var fields = [['cpm', 'input']];
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
                    event.preventDefault();
                    if($('.global-' + field + '-input').is(':hidden')) {
                        var elements = $(this);
                    } else {
                        $('.global-' + field + '-input').hide();
                        $('.global-' + field + '-close').show();

                        $('.app-' + field + '-input').show();
                        $('.app-' + field + '-close').hide();

                        var elements = $('.app-' + field + '-close');
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
                    event.preventDefault();
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

            var MODAL_FIELDS = ([
                ['allocation_percentage', '%, '],
                ['daily_frequency_cap', '/d '],
                ['hourly_frequency_cap', '/h']
            ]);

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
                    text = "None";
                }

                if($(row).hasClass('adunit-row')) {
                    var app_key = app_for_adunit[key];
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

                    $(modal_div).find('.cancel').click(function() {
                        $(modal_div).modal('hide');
                    });
                });
            });

            /* Initialize advanced options and active fields */
            // mimic an entry for each adunit to prepopulate settings
            // at app and global levels
            _.each(_.flatten(_.values(adunits_for_app)), function(adunit_key) {
                var adunit_row = $('#' + adunit_key + '-row')

                // prepopulate advanced options modals
                var modal_div = $('#' + adunit_key +'-options');
                modal_ok(adunit_row, modal_div);
            });


            /*
             * Geographical and Connectivity Targeting
             */

            /* Elements */
            var $targeted_countries = $('#id_targeted_countries');
            var $targeted_regions = $('#id_targeted_regions');
            var $targeted_cities = $('#id_targeted_cities');
            var $targeted_zip_codes = $('#id_targeted_zip_codes');
            var $targeted_carriers = $('#id_targeted_carriers');

            var $region_targeting_type_all = $('#id_region_targeting_type_0');
            var $region_targeting_type_regions_and_cities = $('#id_region_targeting_type_1');
            var $region_targeting_type_zip_codes = $('#id_region_targeting_type_2');

            var $connectivity_targeting_type_all = $('#id_connectivity_targeting_type_0');
            var $connectivity_targeting_type_carriers = $('#id_connectivity_targeting_type_2');

            /* Helpers */
            function update_geographical_and_connectivity_targeting() {
                var targeted_countries = $targeted_countries.val();

                var us_is_targeted = _.include(targeted_countries, 'US');
                var ca_is_targeted = _.include(targeted_countries, 'CA');
                var gb_is_targeted = _.include(targeted_countries, 'GB');
                var wifi_is_targeted = $('input[name="connectivity_targeting_type"]:checked').val() == 'wi-fi';

                update_regions_and_cities(targeted_countries, us_is_targeted, ca_is_targeted, wifi_is_targeted);
                update_zip_codes(us_is_targeted, wifi_is_targeted);
                update_carriers(us_is_targeted, ca_is_targeted, gb_is_targeted);
            }

            function update_regions_and_cities(targeted_countries, us_is_targeted, ca_is_targeted, wifi_is_targeted) {
                if(!targeted_countries) {
                    // change region targeting type
                    if($region_targeting_type_regions_and_cities.is(':checked')) {
                        $region_targeting_type_all.click();
                    }

                    // disable
                    $region_targeting_type_regions_and_cities.attr('disabled', true);
                    $region_targeting_type_regions_and_cities.parent().addClass('muted');
                }
                else {
                    // enable
                    $region_targeting_type_regions_and_cities.removeAttr('disabled');
                    $region_targeting_type_regions_and_cities.parent().removeClass('muted');

                    // update type-ahead AJAX call with selected countries
                    targeted_cities_ajax_data.country = targeted_countries;
                }

                update_regions(us_is_targeted, ca_is_targeted, wifi_is_targeted);
                update_cities(targeted_countries);
            }

            function update_regions(us_is_targeted, ca_is_targeted, wifi_is_targeted) {
                if((!us_is_targeted && !ca_is_targeted) || !wifi_is_targeted) {
                    // clear
                    $targeted_regions.html('');

                    // disable
                    $targeted_regions.attr('disabled', true);
                    $targeted_regions.siblings('label').addClass('muted');
                }
                else {
                    if(us_is_targeted) {
                        add_options($targeted_regions, bootstrapping_data.US_STATES);
                        add_options($targeted_regions, bootstrapping_data.US_METROS);
                    }
                    else {
                        remove_options($targeted_regions, bootstrapping_data.US_STATES);
                        remove_options($targeted_regions, bootstrapping_data.US_METROS);
                    }

                    if(ca_is_targeted) {
                        add_options($targeted_regions, bootstrapping_data.CA_PROVINCES);
                    }
                    else {
                        remove_options($targeted_regions, bootstrapping_data.CA_PROVINCES);
                    }

                    // enable
                    $targeted_regions.removeAttr('disabled');
                    $targeted_regions.siblings('label').removeClass('muted');
                }
                $targeted_regions.trigger("liszt:updated");
            }

            var city_name_regex = /^(.*), (.*), (.*)$/;
            function update_cities(targeted_countries) {
                if(!targeted_countries) {
                    // whenever this is true, this input is hidden.
                }
                else {
                    $('option:selected', $targeted_cities).each(function (index, option) {
                        var $option = $(option);
                        var name = $option.html();
                        var match = city_name_regex.exec(name);
                        // TODO: this is a hack, should use a regex to parse the value
                        var country = match[3];
                        if(!_.include(targeted_countries, country)) {
                            $option.remove();
                        }
                    })
                }
                $targeted_cities.trigger("liszt:updated");
            }

            function update_zip_codes(us_is_targeted, wifi_is_targeted) {
                if(!us_is_targeted || !wifi_is_targeted) {
                    // clear
                    $targeted_zip_codes.val('');

                    // remove selection
                    if($region_targeting_type_zip_codes.is(':checked')) {
                        $region_targeting_type_all.click();
                    }

                    // disable
                    $region_targeting_type_zip_codes.attr('disabled', true);
                    $region_targeting_type_zip_codes.parent().addClass('muted');
                }
                else {
                    // enable
                    $region_targeting_type_zip_codes.removeAttr('disabled');
                    $region_targeting_type_zip_codes.parent().removeClass('muted');
                }
            }

            function update_carriers(us_is_targeted, ca_is_targeted, gb_is_targeted) {
                if(!us_is_targeted && !ca_is_targeted && !gb_is_targeted) {
                    // clear
                    $targeted_carriers.html('');

                    // remove selection
                    if($connectivity_targeting_type_carriers.is(':checked')) {
                        $connectivity_targeting_type_all.click();
                    }

                    // disable
                    $connectivity_targeting_type_carriers.attr('disabled', true);
                    $connectivity_targeting_type_carriers.parent().addClass('muted');
                }
                else {
                    if(us_is_targeted) {
                        add_options($targeted_carriers, bootstrapping_data.US_CARRIERS);
                    }
                    else {
                        remove_options($targeted_carriers, bootstrapping_data.US_CARRIERS);
                    }

                    if(ca_is_targeted) {
                        add_options($targeted_carriers, bootstrapping_data.CA_CARRIERS);
                    }
                    else {
                        remove_options($targeted_carriers, bootstrapping_data.CA_CARRIERS);
                    }

                    if(gb_is_targeted) {
                        add_options($targeted_carriers, bootstrapping_data.GB_CARRIERS);
                    }
                    else {
                        remove_options($targeted_carriers, bootstrapping_data.GB_CARRIERS);
                    }

                    // enable
                    $connectivity_targeting_type_carriers.removeAttr('disabled');
                    $connectivity_targeting_type_carriers.parent().removeClass('muted');
                }
                $targeted_carriers.trigger("liszt:updated");
            }

            function add_options($element, options) {
                for(var index in options) {
                    var value = options[index][0];
                    if(!$('option[value="' + value + '"]', $element).length) {
                        $element.append($('<option />', {
                            value: value,
                            html: options[index][1]
                        }));
                    }
                }
            }

            function remove_options($element, options) {
                for(var index in options) {
                    var value = options[index][0];
                    $('option[value="' + value + '"]', $element).remove();
                }
            }

            /* Event Handlers */
            $targeted_countries.chosen().change(update_geographical_and_connectivity_targeting);

            $('input[name="region_targeting_type"]').click(function () {
                $('input[name="region_targeting_type"]').parent().siblings('div').hide();
                $(this).parent().siblings('div').show();
            });
            $('input[name="region_targeting_type"]:checked').click();

            $targeted_regions.chosen();

            var targeted_cities_ajax_data = {
                featureClass: 'P',
                maxRows: 10,
                username: 'MoPub'
            };
            $targeted_cities.ajaxChosen(
                {
                    data: targeted_cities_ajax_data,
                    dataType: 'json',
                    jsonTermKey: 'name_startsWith',
                    method: 'GET',
                    minTermLength: 3,
                    traditional: true,
                    url: 'http://api.geonames.org/searchJSON'
                }, function (data) {
                    var terms = {};
                    for(var index in data.geonames) {
                        var geoname = data.geonames[index];
                        var key = '(' + geoname.lat + ',' + geoname.lng + ',\'' + geoname.name + '\',\'' + geoname.adminCode1 + '\',\'' + geoname.countryCode + '\')';
                        var value = geoname.name + ', ' + geoname.adminCode1 + ', ' + geoname.countryCode;
                        terms[key] = value;
                    }
                    return terms;
                }
            );

            $('#id_connectivity_targeting_type_1').change(function () {
                $('#id_targeted_carriers').parent().hide();
                update_geographical_and_connectivity_targeting();
            });
            $connectivity_targeting_type_all.click(function () {
                if($targeted_regions.val() || $targeted_zip_codes.val()) {
                    event.preventDefault();
                    $('#target_carriers_warning .continue').unbind().click(function () {
                        $connectivity_targeting_type_all.attr('checked', 'checked');
                        $('#id_targeted_carriers').parent().hide();
                        update_geographical_and_connectivity_targeting();
                    })
                    $('#target_carriers_warning').modal();
                }
                else {
                    update_geographical_and_connectivity_targeting();
                }
            });
            $connectivity_targeting_type_carriers.click(function () {
                if($targeted_regions.val() || $targeted_zip_codes.val()) {
                    event.preventDefault();
                    $('#target_carriers_warning .continue').unbind().click(function () {
                        $connectivity_targeting_type_carriers.attr('checked', 'checked');
                        $('#id_targeted_carriers').parent().show();
                        update_geographical_and_connectivity_targeting();
                    })
                    $('#target_carriers_warning').modal();
                }
                else {
                    $('#id_targeted_carriers').parent().show();
                    update_geographical_and_connectivity_targeting();
                }
            });
            // update on document ready
            if($('input[name="connectivity_targeting_type"]:checked').val() != 'carriers') {
                $('#id_targeted_carriers').parent().hide();
            }

            $targeted_carriers.chosen();

            // TODO: grey out countries when a region or city of theirs is selected

            // Initialize
            update_geographical_and_connectivity_targeting();

            _.each(bootstrapping_data.targeted_regions, function (targeted_region) {
                $('option[value="' + targeted_region + '"]', $targeted_regions).prop('selected', 'selected');
            })
            $targeted_regions.trigger("liszt:updated");

            var city_tuple_regex = /^\((.*),(.*),'(.*)','(.*)','(.*)'\)$/;
            _.each(bootstrapping_data.targeted_cities, function (targeted_city) {
                var match = city_tuple_regex.exec(targeted_city);
                var name = match[3] + ', ' + match[4] + ', ' + match[5];
                $targeted_cities.append($('<option />', {
                    html: name,
                    selected: 'selected',
                    value: targeted_city
                }));
            });
            $targeted_cities.trigger("liszt:updated");

            _.each(bootstrapping_data.targeted_carriers, function (targeted_carrier) {
                $('option[value="' + targeted_carrier + '"]', $targeted_carriers).prop('selected', 'selected');
            })
            $targeted_carriers.trigger("liszt:updated");


            /*
             * Device Targeting
             */

            $('input[name="device_targeting"]').change(function () {
                if($(this).val() == '0') {
                    $('#device_targeting_details').slideUp();
                }
                else {
                    $('#device_targeting_details').slideDown();
                }
            });
            // update on document ready
            if($('input[name="device_targeting"]:checked').val() == '0') {
                $('#device_targeting_details').hide();
            }


            // initial form items saved in hash
            if(campaign_key) {
                var startItems = convertSerializedArrayToHash($('form#campaign_and_adgroup').serializeArray());
            }
        }
    };

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
            var campaigns = new Campaigns(all_campaigns);

            new NetworkGraphView({
                collection: campaigns,
                start_date: graph_start_date,
                line_graph: true,
                mopub_optimized: false,
            });

            initialize_show_network();

            $('.chzn-select').chosen({no_results_text: "No results matched"});

            $('#delete-network')
                .click(function () {
                                $.post('/networks/delete',
                                    {campaign_key: campaign_data.id},
                                    function() {
                                      window.location = '/networks';
                                });
            });

            $('#network-editActive').change(function () {
                $('#active-spinner').show();
                $.post('/networks/pause',
                       { campaign_key: campaign_data.id,
                         active: $(this).val() } ,
                       function(data) {
                           $('#active-spinner').hide();
                       });
            });

            }
    };

    window.NetworkDetailsController = NetworkDetailsController;
    window.NetworksController = NetworksController;
    window.EditNetworkController = EditNetworkController;

})(this.jQuery, this._);

