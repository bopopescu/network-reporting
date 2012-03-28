$(function() {
    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    var initialize_campaign_data = function(campaign_data, include_adunits, ajax_query_string) {
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

    var initialize_show_network = function() {
        $('#show-network').change(function() {
            if ($(this).is(':checked')) {
                $('.network-data').show();
                mopub.Chart.trafficChart.series[1].show();
            } else {
                $('.network-data').hide();
                mopub.Chart.trafficChart.series[1].hide();
            }
        });
    }

    var NetworksController = { 
        initialize: function(bootstrapping_data) {
            var campaigns_data = bootstrapping_data.campaigns_data,
                date_range = bootstrapping_data.date_range,
                graph_start_date = bootstrapping_data.graph_start_date,
                networks = bootstrapping_data.networks,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            var all_campaigns = []
            _.each(campaigns_data, function(campaign_data) {
                all_campaigns = all_campaigns.concat(initialize_campaign_data(campaign_data, false, ajax_query_string));
            });

            var campaigns = new Campaigns(all_campaigns);

            // Load chart
            var graph_view = new NetworkGraphView({
                collection: campaigns,
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
                    $(this).text("Hide Apps");
                } else {
                    div.hide()
                    $(this).text("Show Apps");
                }
            });

            $('#network-editSelect').change(function() {
                if ($(this).val()) {
                    window.location = $(this).val();
                }
                $(this).selectmenu('index', 0);
            });

            $('#network-editSelect-menu').find('li').first().hide();

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
                        //$('#networkForm').submit();
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

    var NetworkDetailsController = { 
        initialize: function(bootstrapping_data) {
            var campaign_data = bootstrapping_data.campaign_data,
                graph_start_date = bootstrapping_data.graph_start_date,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            var all_campaigns = initialize_campaign_data(campaign_data, true, ajax_query_string);

            // create campaigns collection
            campaigns = new Campaigns(all_campaigns);

            var graph_view = new NetworkGraphView({
                collection: campaigns,
                type: 'details',
                start_date: graph_start_date,
                line_graph: true,
                mopub_optimized: false,
            });

            initialize_show_network();

            $('#network-settingsButton')
                .button({ icons: { primary: "ui-icon-wrench" } })

            $('#delete-network')
                .button({ icons: { primary: "ui-icon-trash" } })
                .click(function () {
                    var key = $(this).attr('id');
                    var div = $('.' + key);
                    div.dialog({
                        buttons: {
                            "Delete": function() { window.location = '/networks/delete/' + campaign_data.id; },
                            "Cancel": function() { $(this).dialog('close');} }
                    });
                });

            $('#network-editActive').change(function () {
                var hidden_li = $('#network-editActive-menu').find('li:hidden');
                var shown_li = $('#network-editActive-menu').find('li:not(:hidden)');
                hidden_li.show();
                shown_li.hide();
                var val = $(this).val(); 
                if (val == 'active') {
                    $('#network-activeImage').show();
                    $('#network-pausedImage').hide();
                } else {
                    $('#network-pausedImage').show();
                    $('#network-activeImage').hide();
                }

                $.post('/networks/pause/' + campaign_data.id, { active: val } );
            });

            $('#network-editActive-menu').find('li').first().hide();

            }
    }

    window.NetworkDetailsController = NetworkDetailsController;
    window.NetworksController = NetworksController;
});

