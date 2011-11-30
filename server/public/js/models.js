(function($, Backbone, _) {

    /*
     * ## Stats Models
     */

    var Stats = Backbone.Model.extend({
        defaults: {
            revenue: 0,
            clicks: 0,
            impressions: 0
        }
    });

    var MpxStats = Stats.extend({

    });

    var DirectSoldStats = Stats.extend({

    });

    var NetworkStats = Stats.extend({

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
            active: false,
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
            active: false,
            attempts: 0,
            clicks: 0,
            ctr: 0,
            ecpm: 0,
            fill_rate: 0,
            impressions: 0,
            name: '',
            price_floor: 0,
            revenue: 0
        },
        calcCtr: function () {
            return (this.get('clicks') / (this.get('impressions')+1));
        },
        calcEcpm: function () {
            return (this.get('revenue') / (this.get('impressions')+1)*1000);
        },
        calcFillRate: function () {
            if (attempts === 0) {
                return 0.0;
            }
            return (impressions/attempts)*100;
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
            revenue: 0,
            attempts: 0,
            icon_url: "/placeholders/image.gif",
            impressions: 0,
            fill_rate: 0,
            clicks: 0,
            price_floor: 0,
            app_type: 'iOS',
            ecpm: 0,
            ctr: 0
        },
        url: function () {
            return '/api/app/' + this.id + "?"  + window.location.search.substring(1);
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