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
            console.log('campaigns');
            console.log(campaigns);
            console.log(campaigns.get_total_daily_stats('attempt_count'));

            // Load chart
            var graph_view = new CollectionGraphView({
                collection: campaigns,
                start_date: graph_start_date,
                today: today,
                yesterday: yesterday,
                line_graph: false,
                mopub_optimized: false,
            });
            graph_view.render();

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
                console.log('network_apps');
                console.log(network_apps);
                var network_apps_view = new NetworkAppsView({
                    collection: network_apps
                });
                network_apps.fetch({
                    data: ajax_query_string,
                });

                console.log(network_apps.length);
            });
        }
    }

    var NetworkDetailsController = { 
        initialize: function(bootstrapping_data) {
            var campaign_data = bootstrapping_data.campaign_data,
                network_data = bootstrapping_data.network_data,
                adgroups_data = bootstrapping_data.adgroups_data,
                graph_start_date = bootstrapping_data.graph_statr_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            var adgroups = new AdGroups(adgroups_data);

//            var graph_view = new CollectionGraphView({
//                collection: adgroups,
//                start_date: graph_start_date,
//                today: today,
//                yesterday: yesterday
//            });
//            graph_view.render();

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

            console.log('network_data');
            console.log(network_data);
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
            console.log('network_apps');
            console.log(network_data.name);
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

