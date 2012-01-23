$(function() {
	AdNetworkReportsController = function(networks_data, apps_data, ajax_query_string) {
        // Load account level roll up stats
        var account_roll_up = new AccountRollUp();
        var account_roll_up_view = new AccountRollUpView({
            model: account_roll_up,
        });
        account_roll_up.fetch({ data: ajax_query_string });

        // Load graph data
        var daily_stats = new DailyStatsCollection();
        var daily_stats_view = new DailyStatsView({
            collection: daily_stats,
        });
        daily_stats.fetch({ data: ajax_query_string });

        // Load rolled up network stats
        for(i=0; i < networks_data.length; i++) {
            var network_data = networks_data[i];
            if(network_data['models'].length > 0) { 
                var roll_up = new RollUp({id: network_data['network'],
                                          type: 'network',
                });
                var roll_up_view = new RollUpView({
                    model: roll_up,
                });
                roll_up.fetch({ data: ajax_query_string });
            }
        }

        // Load rolled up apps stats
        for(i=0; i < apps_data.length; i++) {
            var app_data = apps_data[i];
            var roll_up = new RollUp({id: app_data['id'],
                                      type: 'app',});
            var roll_up_view = new RollUpView({
                model: roll_up,
            });
            roll_up.fetch({ data: ajax_query_string });
        }

        // Load stats for app on network
        for(i=0; i < networks_data.length; i++) {
            var network_data = networks_data[i];
            if(network_data['models'].length > 0) { 
                var apps_on_network = new AppOnNetworkCollection(network_data['models']);
                apps_on_network.each(function(app_on_network) {
                    var app_on_network_view = new AppOnNetworkView({
                        model: app_on_network,
                    });
                    app_on_network.fetch({data: ajax_query_string,});
                });
            }
        }
    };
});
