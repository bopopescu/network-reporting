$(function() {
    // TODO: document
    /*
     *   adgroups_data
     *   graph_start_date
     *   today
     *   yesterday
     *   ajax_query_string
     */

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
                console.log(campaign)
            });


            // Load rolled up network stats
            $.each(networks, function(index, network) {
                var roll_up = new RollUp({
                    id: network,
                    type: 'network'
                });
                var roll_up_view = new RollUpView({
                    model: roll_up
                });
                roll_up.fetch({ data: ajax_query_string });
            });
        }
    }

    window.NetworksController = NetworksController;
});

