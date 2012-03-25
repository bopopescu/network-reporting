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
                graph_start_date = bootstrapping_data.graph_start_date,
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
                network = bootstrapping_data.network,
                reporting = bootstrapping_data.reporting,
                graph_start_date = bootstrapping_data.graph_start_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            // get mopub campaign data
            // endpoint=all
            campaign_data.name = 'From MoPub';
            var mopub_campaign = new Campaign(campaign_data);

            // get network campaign data
            // endpoint=network
            if (reporting) {
                var network_campaign_data = jQuery.extend({}, campaign_data);
                network_campaign_data.stats_endpoint = 'networks';
                network_campaign_data.name = 'From Networks';
                var network_campaign = new Campaign(network_campaign_data);

                // create campaigns collection
                campaigns = new Campaigns([mopub_campaign, network_campaign]);
            } else {
                // create campaigns collection
                campaigns = new Campaigns([mopub_campaign]);
            }


            var graph_view = new CollectionGraphView({
                collection: campaigns,
                start_date: graph_start_date,
                today: today,
                yesterday: yesterday,
                line_graph: true,
                mopub_optimized: false,
            });
            graph_view.render();

            new CampaignView({
                model: mopub_campaign
            });
            campaigns.each(function(campaign) {
                campaign.fetch({
                    data: ajax_query_string,
                    error: function () {
                        campaign.fetch({
                            error: toast_error
                        });
                    }
                });
            });

            // TODO: remove this shit, stop loopin over networks
            // Load rolled up network stats
            var roll_up = new RollUp({
                id: network,
                type: 'network'
            });
            var roll_up_view = new RollUpView({
                model: roll_up
            });
            roll_up.fetch({ data: ajax_query_string });
            

            // Load NetworkApps Collections
            var network_apps = new NetworkApps();

            network_apps.network = network;
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

