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
        campaign_data.name = 'From MoPub';
        var mopub_campaign = new Campaign(campaign_data);

        var all_campaigns = [mopub_campaign];

        // create network campaign
        // endpoint=network
        if (campaign_data.reporting) {
            // Create copy of campaign_data
            var network_campaign_data = jQuery.extend({}, campaign_data);
            network_campaign_data.stats_endpoint = 'networks';
            network_campaign_data.name = 'From Networks';
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

    var NetworksController = { 
        initialize: function(bootstrapping_data) {
            var campaigns_data = bootstrapping_data.campaigns_data,
                date_range = bootstrapping_data.date_range,
                graph_start_date = bootstrapping_data.graph_start_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
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
                today: today,
                yesterday: yesterday,
                line_graph: false,
                mopub_optimized: false,
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

            var all_campaigns = initialize_campaign_data(campaign_data, true, ajax_query_string);

            // create campaigns collection
            campaigns = new Campaigns(all_campaigns);

            var graph_view = new CollectionGraphView({
                collection: campaigns,
                start_date: graph_start_date,
                today: today,
                yesterday: yesterday,
                line_graph: true,
                mopub_optimized: false,
            });
        }
    }

    window.NetworkDetailsController = NetworkDetailsController;
    window.NetworksController = NetworksController;
});

