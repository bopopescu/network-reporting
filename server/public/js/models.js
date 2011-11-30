(function($, Backbone, _) {

    /*
     * ## Stats Models
     */

    // Notes:
    // id is the same as the object's parent (app, adunit, campaign)
    var Stats = Backbone.Model.extend({
        defaults: {
            revenue: 0,
            clicks: 0,
            impressions: 0,
            attempts: 0,
            kind: "app" // can be "campaign" or "adunit"
        },
        ctr: function () {
            return (this.get('clicks') / (this.get('impressions')+1));
        },
        ecpm: function () {
            return (this.get('revenue') / (this.get('impressions')+1)*1000);
        },
        fill_rate: function () {
            if (attempts === 0) {
                return 0.0;
            }
            return (impressions/attempts)*100;
        }
    });

    var MpxStats = Stats.extend({
        defaults: {
            price_floor: 0,
            active: false
        },
        url: function () {
            return '/api/'
                + this.get('kind')
                + '/'
                + this.id
                + '?'
                + window.location.search.substring(1);
        }
    });

    var DirectSoldStats = Stats.extend({
        url: function () {
        }
    });

    var NetworkStats = Stats.extend({
        url: function () {
        }
    });


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
     * ## AdUnit
     */
    var AdUnit = Backbone.Model.extend({
        // If we don't set defaults, the templates will explode
        defaults : {
            name: '',
            mpx_stats: new MpxStats({kind: 'app'}),
            direct_sold_stats: new DirectSoldStats({kind: 'app'}),
            network_stats: new NetworkStats({kind: 'app'})
        },
        url: function() {
            // window.location.search.substring(1) is used to preserve date ranges from the url
            // this makes the fetching work with the datepicker.
            return '/api/app/' + this.app_id + '/adunits/' + this.id + '?' + window.location.search.substring(1);
        }
    });


    var AdUnitCollection = Backbone.Collection.extend({
        model: AdUnit,
        url: function() {
            // window.location.search.substring(1) is used to preserve date ranges from the url
            // this makes the fetching work with the datepicker.
            return '/api/app/' + this.app_id + '/adunits/?' + window.location.search.substring(1);
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
            mpx_stats: new MpxStats({kind: 'app'}),
            direct_sold_stats: new DirectSoldStats({kind: 'app'}),
            network_stats: new NetworkStats({kind: 'app'})
        },
        url: function () {
            return '/api/app/' + this.id + "?"  + window.location.search.substring(1);
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            return response[0];
        },
        initialize: function() {
            this.get('mpx_stats').id = this.id;
        }

    });

    /*
     * ## AppCollection
     */
    var AppCollection = Backbone.Collection.extend({
        model: App,
        // If an app key isn't passed to the url, it'll return a list of all of the apps for the account
        url: '/api/app/',
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