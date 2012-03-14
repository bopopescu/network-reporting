/*
 * # models.js
 *
 * Backbone models
 */

/*jslint browser:true,
  fragment: true,
  maxlen: 110,
  nomen: true,
  indent: 4,
  vars: true,
  white: true
 */

var mopub = mopub || {};

(function ($, Backbone, _) {
    "use strict";

    /*
     * Helper functions for stats
     */
    function calculate_ctr(impression_count, click_count) {
        if (impression_count === null || click_count === null) {
            return null;
        }
        return (impression_count === 0) ? 0 : click_count / impression_count;
    }

    function calculate_fill_rate(request_count, impression_count) {
        if (request_count === null || impression_count === null) {
            return null;
        }
        return (request_count === 0) ? 0 : impression_count / request_count;
    }


    var StatsMixin = {
        get_formatted_stat: function (stat) {
            var value = this.get(stat);
            if (value === null || value === undefined) {
                return '--';
            }
            switch (stat) {
              case 'clicks':
              case 'conversions':
              case 'goal':
              case 'impressions':
              case 'requests':
                return mopub.Utils.formatNumberWithCommas(value);
              case 'cpm':
              case 'revenue':
                return '$' + mopub.Utils.formatNumberWithCommas(value.toFixed(2));
              case 'conv_rate':
              case 'ctr':
              case 'fill_rate':
                return mopub.Utils.formatNumberAsPercentage(value);
              case 'status':
                return value;
              case 'pace':
                return (value*100).toFixed() + '%';
            default:
                throw 'Unsupported stat "' + stat + '".';
            }
        }
        
    };




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
        validate: function(attributes) {
            if (typeof(attributes.price_floor) !== 'undefined') {
                var valid_number = Number(attributes.price_floor);
                if (isNaN(valid_number)) {
                    return "Please enter a valid number for the price floor";
                }
            }
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

    /*
     * ## AdUnitCollection
     *
     * Should collections be named 'collection' or should we pluralize their
     * model name?
     */
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
            app_type: '',
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
            var app = response[0];

            if (app.app_type === 'iphone') {
                app.app_type = 'iOS';
            }
            if (app.app_type === 'android') {
                app.app_type = 'Android';
            }
            if (app.app_type === 'mweb') {
                app.app_type = 'Mobile Web';
            }
            return app;
        },
        get_summed: function (attr) {
            if (typeof(this.get(attr)) !== 'undefined') {
                var series = this.get(attr);
                var sum = _.reduce(series, function(memo, num){
                    return memo + num;
                }, 0);
                return sum;
            }
            return null;
        }
    });

    /*
     * ## AppCollection
     */
    var AppCollection = Backbone.Collection.extend({
        model: App,
        // If an app key isn't passed to the url, it'll return a list
        // of all of the apps for the account
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/app/' +
                '?' + window.location.search.substring(1) +
                '&endpoint=' + stats_endpoint;
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



    /*
     *  AdGroup
     */

    var AdGroup = Backbone.Model.extend({
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/adgroup/' 
                + this.id
                + "?"
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        }
    });

    _.extend(AdGroup, StatsMixin);

    var Campaign = Backbone.Model.extend({
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/campaign/' 
                + this.id
                + "?"
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        }
    });

    _.extend(Campaign.prototype, StatsMixin);

    var CampaignCollection = Backbone.Collection.extend({
        model: Campaign,
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/campaign/'
                + "?"
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        }
    });




    /*
     * EXPOSE HIS JUNK
     * (We should find a better way to do this.)
     */
    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;
    window.AdGroup = AdGroup;
    window.Campaign = Campaign;
    window.CampaignCollection = CampaignCollection;

}(this.jQuery, this.Backbone, this._));