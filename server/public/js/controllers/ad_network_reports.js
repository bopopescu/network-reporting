$(function() {
	AdNetworkReportsController = function(networks_data, apps_data, ajax_query_string) {
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
            console.log(network_data['models']);
            if(network_data['models'].length > 0) { 
                var apps_on_network = new AppOnNetworkCollection(network_data['models']);
                var app_on_network_view = new AppOnNetworkView({
                    collection: apps_on_network,
                });
                apps_on_network.each(function(app_on_network) { app_on_network.fetch({ data: ajax_query_string }); });
            }
        }
    };
});
