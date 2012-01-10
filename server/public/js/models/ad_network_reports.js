(function($, Backbone, _) {

    /*
     * ## NetworkStats
     * This model holds the ad network reporting data for either an application
     * or an ad network.
     */
    var RollUp = Backbone.Model.extend({
        defaults : {
            revenue: 0,
            attempts: 0,
            impressions: 0,
            cpm: 0,
            fill_rate: 0,
            clicks: 0,
            cpc: 0,
            ctr: 0,
        },
        url: function () {
            return '/api/roll_up/'
                + this.get('type')
                + '/id/'
                + this.id
        },
    });

    /*
     * ## AppOnNetwork
     * This model holds the ad network reporting data for an application on a a specific network.
     */
    var AppOnNetwork = Backbone.Model.extend({
        defaults : {
            name: '',
            revenue: 0,
            attempts: 0,
            impressions: 0,
            cpm: 0,
            fill_rate: 0,
            clicks: 0,
            cpc: 0,
            ctr: 0,
        },
        url: function () {
            return '/api/app_on_network/'
                + this.get('network')
                + '/pub_id/'
                + this.id;
        },
    });

    /*
     * ## AppOnNetworkCollection
     */
    var AppOnNetworkCollection = Backbone.Collection.extend({
        model: AppOnNetwork,
    });

    window.RollUp = RollUp;
    window.AppOnNetworkCollection = AppOnNetworkCollection;
    window.AppOnNetwork = AppOnNetwork;


})(this.jQuery, this.Backbone, this._);
