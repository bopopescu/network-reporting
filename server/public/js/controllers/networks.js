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
            var campaigns_data = bootstrapping_data.campaigns_data,
                graph_start_date = bootstrapping_data.graph_start_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                networks = bootstrapping_data.networks,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            mopub_campaigns = []
            network_campaigns = []
            _.each(campaigns_data, function(campaign_data) {
                // create mopub campaign
                // endpoint=all
                campaign_data.name = 'From MoPub';
                var mopub_campaign = new Campaign(campaign_data);

                var campaigns_list = []

                // create network campaign
                // endpoint=network
                if (campaign_data.reporting) {
                    var network_campaign_data = jQuery.extend({}, campaign_data);
                    network_campaign_data.stats_endpoint = 'networks';
                    network_campaign_data.name = 'From Networks';
                    var network_campaign = new Campaign(network_campaign_data);

                    campaigns_list = [mopub_campaign, network_campaign];
                } else {
                    campaigns_list = [mopub_campaign];
                }

                // Create CampaignView and fetch mopub campaign and network
                // campaign if campaign has reporting
                _.each(campaigns_list, function(campaign) {
                    console.log(campaign.get('stats_endpoint'));
                    new CampaignView({
                        model: campaign
                    });

                    campaign.fetch({ data: ajax_query_string, });
                });

                // Load NetworkApps Collections
                var network_apps = new NetworkApps();

                network_apps.campaign_key = campaign_data.id;

                network_apps.network = campaign_data.network;
                var network_apps_view = new NetworkAppsView({
                    collection: network_apps
                });
                network_apps.fetch({ data: ajax_query_string, });
            });

            //var campaigns = new Campaigns(campaign_data);

            // Load chart
//            var graph_view = new CollectionGraphView({
//                collection: campaigns,
//                network_stats: network_stats,
//                start_date: graph_start_date,
//                today: today,
//                yesterday: yesterday,
//                line_graph: false,
//                mopub_optimized: false,
//            });
//            graph_view.render();

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
            new CampaignView({
                model: network_campaign
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

