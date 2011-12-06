(function($, Backbone, _) {

    /*
     * ## Campaigns
     */
    var Campaign = Backbone.Model.extend({
        defaults: {
            name: '',
            budget: 0.0,
            budget_type: '',
            start_datetime: new Date(),
            end_datetime: null,
            active: false
        }
    });

    var GuaranteedCampaign = Campaign.extend({

    });

    var PromoCampaign = Campaign.extend({

    });

    var NetworkCampaign = Campaign.extend({

    });

    var Targeting = Backbone.Model.extend({
        // for future use?
    });


    /*
     * ## AdGroups
     */

    /*
     * Helper Functions
     */
    // TODO: finish adding cases for all stats
    format_stat = function(stat, value) {
        if(value === null) return '--';
        switch(stat) {
            case 'click_count':
            case 'impression_count':
            case 'conversion_count':
            case 'request_count':
                return mopub.Utils.formatNumberWithCommas(value);
            case 'revenue':
                return '$' + mopub.Utils.formatNumberWithCommas(value.toFixed(2));
            case 'fill_rate':
                return mopub.Utils.formatNumberAsPercentage(value);
            case 'ctr':
                return mopub.Utils.formatNumberAsPercentage(value);
            case 'ecpm':
            case 'attempts':
            default:
                return value;
        }
    }

    /*
     *
     */
    AdGroup = Backbone.Model.extend({
        get_stat: function(stat) {
            if(!this.has(stat)) return null;
            return this.get(stat);
        },

        get_formatted_stat: function(stat) {
            return format_stat(stat, this.get_stat(stat));
        }
    });

    /*
     *  
     */
    AdGroups = Backbone.Collection.extend({
        model: AdGroup,

        get_stat_sum: function(stat) {
            return this.reduce(function(memo, adgroup) {
                if(memo === null || !adgroup.has(stat)) return null;
                return memo + adgroup.get(stat);
            }, 0);
        },

        // TODO: add cases for calculated stats (ctr, fill_rate, etc.)
        get_stat: function(stat) {
            switch(stat) {
                default:
                    return this.get_stat_sum(stat);
            }
        },

        get_formatted_stat: function(stat) {
            //alert('' + stat + ': ' + this.get_stat(stat));
            return format_stat(stat, this.get_stat(stat));
        },

        // TODO: make this less hacky
        isFullyLoaded: function() {
            return this.reduce(function(memo, adgroup) { return memo && adgroup.has('impression_count') }, true);
        }
    });


    /*
     * ## AdUnit
     */
    var AdUnit = Backbone.Model.extend({
        // If we don't set defaults, the templates will explode
        defaults : {
            active: false,
            attempts: 0,
            clicks: 0,
            ctr: 0,
            ecpm: 0,
            fill_rate: 0,
            impressions: 0,
            name: '',
            price_floor: 0,
            requests: 0,
            revenue: 0,
            stats_endpoint: 'all'
        },
        url: function() {
            // window.location.search.substring(1) is used to preserve date ranges from the url
            // this makes the fetching work with the datepicker.
            var stats_endpoint = this.get('stats_endpoint');
            return '/api/app/'
                + this.app_id
                + '/adunits/'
                + this.id
                + '?'
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        }
    });


    var AdUnitCollection = Backbone.Collection.extend({
        model: AdUnit,
        url: function() {
            // window.location.search.substring(1) is used to preserve date ranges from the url
            // this makes the fetching work with the datepicker.
            var stats_endpoint = this.stats_endpoint;
            return '/api/app/'
                + this.app_id
                + '/adunits/'
                + '?'
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        }
    });


    /*
     * ## App
     * We might consider turning derivative values (ecpm, fill_rate, ctr) into
     * functions.
     */
    var App = Backbone.Model.extend({
        defaults : {
            name: '',
            url:'#',
            icon_url: "/placeholders/image.gif",
            app_type: 'iOS',
            active: false,
            attempts: 0,
            clicks: 0,
            ctr: 0,
            ecpm: 0,
            fill_rate: 0,
            impressions: 0,
            price_floor: 0,
            requests: 0,
            revenue: 0,
            stats_endpoint: 'all'
        },
        url: function () {
            var stats_endpoint = this.get('stats_endpoint');
            return '/api/app/'
                + this.id
                + "?"
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            return response[0];
        }
    });

    /*
     * ## AppCollection
     */
    var AppCollection = Backbone.Collection.extend({
        model: App,
        // If an app key isn't passed to the url, it'll return a list of all of the apps for the account
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/app/' +
                + '?'
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        },
        // Not used anymore, but could come in handy
        fetchAdUnits: function() {
            this.each(function (app) {
                app.adunits = new AdUnitCollection();
                app.adunits.app_id = app.id;
                app.adunits.fetch();
            });
        }
    });


    // Globalize. We should find a better way to do this.
    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;

})(this.jQuery, this.Backbone, this._);