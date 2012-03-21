$(function() {
    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    var NetworksController = { 
        initialize: function(bootstrapping_data) {
            var campaign_data = bootstrapping_data.campaign_data,
                graph_start_date = bootstrapping_data.graph_statr_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                networks = bootstrapping_data.networks,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            var campaigns = new Campaigns(campaign_data);
            var network_stats = new DailyStatsCollection();

            // Load chart
            var graph_view = new NetworkGraphView({
                collection: campaigns,
                network_stats: network_stats,
                start_date: graph_start_date,
                today: today,
                yesterday: yesterday,
                line_graph: false,
                mopub_optimized: false,
            });
            graph_view.render();

            // Load network collected stats for graph
            network_stats.fetch({ data: ajax_query_string });

            // Load mopub collected StatsModel stats keyed on campaign
            campaigns.each(function(campaign) {
                new CampaignView({
                    model: campaign
                });
                campaign.fetch({
                    data: ajax_query_string,
                    error: function () {
                        campaign.fetch({
                            error: toast_error
                        });
                    }
                });
            });

            // Load rolled up network stats
            $.each(networks, function(index, network) {
                var network = new RollUp({
                    id: network,
                    type: 'network'
                });
                new RollUpView({
                    model: network
                });
                network.fetch({
                    data: ajax_query_string,
                });
            });


            // Load NetworkApps Collections
            // TODO: Possibly include rolled up data
            $.each(networks, function(index, network) {
                var network_apps = new NetworkApps();

                network_apps.network = network;
                var network_apps_view = new NetworkAppsView({
                    collection: network_apps
                });
                network_apps.fetch({
                    data: ajax_query_string,
                });

            });
        }
    }

    var NetworkDetailsController = { 
        initialize: function(bootstrapping_data) {
            var campaign_data = bootstrapping_data.campaign_data,
                network_data = bootstrapping_data.network_data,
                graph_start_date = bootstrapping_data.graph_statr_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            var network_details = new NetworkDetailsDailyStats();
            network_details.network = network_data.name;
            network_details.fetch({ data: ajax_query_string });

            var graph_view = new CollectionGraphView({
                collection: network_details,
                start_date: graph_start_date,
                today: today,
                yesterday: yesterday,
                line_graph: true,
                mopub_optimized: false,
            });
            graph_view.render();

            var campaign = new Campaign(campaign_data);
            new CampaignView({
                model: campaign
            });
            campaign.fetch({
                data: ajax_query_string,
                error: function () {
                    campaign.fetch({
                        error: toast_error
                    });
                }
            });

            // TODO: remove this shit, stop loopin over networks
            // Load rolled up network stats
            var roll_up = new RollUp({
                id: network_data.name,
                type: 'network'
            });
            var roll_up_view = new RollUpView({
                model: roll_up
            });
            roll_up.fetch({ data: ajax_query_string });
            
            // Load stats for app on network
            var apps_on_network = new AppOnNetworkCollection(network_data.models);
            apps_on_network.each(function(app_on_network) {
                var app_on_network_view = new AppOnNetworkView({
                    model: app_on_network
                });
                app_on_network.fetch({ data: ajax_query_string });
            });


            // Load NetworkApps Collections
            // TODO: Render inline
            var network_apps = new NetworkApps();

            network_apps.network = network_data.name;
            network_apps.type = 'adunits';
            var network_apps_view = new NetworkAppsView({
                collection: network_apps
            });
            network_apps.fetch({
                data: ajax_query_string,
            });
        }
    }

    window.NetworkDetailsController = NetworkDetailsController;
    window.NetworksController = NetworksController;
});

