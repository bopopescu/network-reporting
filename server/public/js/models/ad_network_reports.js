(function($, Backbone, _) {

    /*
     * ## AccountRollUp
     * This model holds the rolled up ad network reporting data for an account
     */
    var AccountRollUp = Backbone.Model.extend({
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
            return '/api/ad_network/account_roll_up/';
        },
    });

    /*
     * ## DailyStatsCollection
     * Holds the stats to render the chart.
     */
    var DailyStatsCollection = Backbone.Collection.extend({
        model: AppOnNetwork,

        get_daily_stats: function (stat) {
            return _.map(this.models, function(model){
                return model.get(stat);
            });
        },

        url: function () {
            return '/api/ad_network/daily_stats/';
        },
    });

    /*
     * ## RollUp
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
            return '/api/ad_network/roll_up/'
                + this.get('type')
                + '/id/'
                + this.id;
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
            return '/api/ad_network/app_on_network/'
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

    window.AccountRollUp = AccountRollUp;
    window.DailyStatsCollection = DailyStatsCollection;
    window.RollUp = RollUp;
    window.AppOnNetwork = AppOnNetwork;
    window.AppOnNetworkCollection = AppOnNetworkCollection;


})(this.jQuery, this.Backbone, this._);
