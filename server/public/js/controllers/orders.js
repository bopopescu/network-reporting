(function () {
    "use strict";

    var OrdersController = {
        initializeIndex: function(bootstrapping_data) {
            // Create a campaign collection for the account
            var campaigns = new CampaignCollection();
            campaigns.stats_endpoint = 'direct';

            // Once the campaigns have been fetched, render them.
            campaigns.bind('reset', function(campaigns_collection) {
                _.each(campaigns_collection.models, function(campaign) {
                    var campaign_view = CampaignView({
                        model: campaign,
                        el: 'orders_table'
                    });
                    campaign_view.renderInline();
                });
            });

            // Fetch the campaigns
            campaigns.fetch();
        },

        initializeOrderDetail: function(bootstrapping_data) {
            
        },

        initializeLineItemDetail: function(bootstrapping_data) {
            
        },

        initializeOrderForm: function(bootstrapping_data) {
            
        },


        initializeLineItemForm: function(bootstrapping_data) {
                    
        }
    };

    mopub.Controllers.OrdersController = OrdersController;

})(window.jQuery, window.mopub || { Controllers: {} });