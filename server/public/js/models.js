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

    function format_stat(stat, value) {
        if (value === null) {
            return '--';
        }
        switch (stat) {
          case 'click_count':
          case 'conversion_count':
          case 'goal':
          case 'impression_count':
          case 'request_count':
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
        default:
            throw 'Unsupported stat "' + stat + '".';
        }
    }

    /*
     * ## AdGroup model
     * This will most likely need to be refactored soon when we change how
     * AdGroups work on the backend.
     */

    var AdGroup = Backbone.Model.extend({
        get_stat: function(stat) {
            if (!this.has(stat)) {
                return null;
            }
            return this.get(stat);
        },

        get_formatted_stat: function(stat) {
            return format_stat(stat, this.get_stat(stat));
        },

        get_stat_for_day: function(stat, day) {
            if (!this.has("daily_stats")) {
                return null;
            }
            var daily_stats = this.get("daily_stats");
            if (day >= daily_stats.length) {
                return null;
            }
            var day_stats = daily_stats[day];
            if (!stat in day_stats) {
                return null;
            }
            return day_stats[stat];
        },

        url: function() {
            return '/api/adgroup/' + this.id;
        }
    });


    /*
     * ## Adgroup Collection
     */
    var AdGroups = Backbone.Collection.extend({
        model: AdGroup,

        get_stat_sum: function(stat) {
            return this.reduce(function(memo, adgroup) {
                if (memo === null || !adgroup.has(stat)) {
                    return null;
                }
                return memo + adgroup.get(stat);
            }, 0);
        },

        get_stat: function(stat) {
            switch(stat) {
                case 'ctr':
                    return calculate_ctr(this.get_stat('impression_count'),
                                         this.get_stat('click_count'));
                case 'fill_rate':
                    return calculate_fill_rate(this.get_stat('request_count'),
                                               this.get_stat('impression_count'));
                case 'click_count':
                case 'conversion_count':
                case 'impression_count':
                case 'request_count':
                case 'revenue':
                    return this.get_stat_sum(stat);
                default:
                    throw 'Unsupported stat "' + stat + '".';
            }
        },

        get_formatted_stat: function(stat) {
            return format_stat(stat, this.get_stat(stat));
        },

        get_stat_sum_for_day: function(stat, day) {
            return this.reduce(function(memo, adgroup) {
                if (memo === null ||
                    !adgroup.has('daily_stats') ||
                    day >= adgroup.get('daily_stats').length ||
                    !(stat in adgroup.get('daily_stats')[day])) {
                    return null;
                }

                return memo + adgroup.get('daily_stats')[day][stat];
            }, 0);
        },

        get_stat_for_day: function(stat, day) {
            switch(stat) {
                case 'ctr':
                    return calculate_ctr(this.get_stat_for_day('impression_count', day),
                                         this.get_stat_for_day('click_count', day));
                case 'fill_rate':
                    return calculate_fill_rate(this.get_stat_for_day('request_count', day),
                                               this.get_stat_for_day('impression_count', day));
                case 'click_count':
                case 'conversion_count':
                case 'impression_count':
                case 'request_count':
                case 'revenue':
                    return this.get_stat_sum_for_day(stat, day);
                default:
                    throw 'Unsupported stat "' + stat + '".';
            }
        },

        get_formatted_stat_for_day: function(stat, day) {
            return format_stat(stat, this.get_stat_for_day(stat, day));
        },

        get_total_daily_stats: function(stat) {
            var total_daily_stats = [];
            var day;
            for(day in this.at(0).get('daily_stats')) {
                total_daily_stats.push(this.get_stat_for_day(stat, day));
            }
            return total_daily_stats;
        },

        get_chart_data: function(stat) {
            var adgroups = this.filter(function(adgroup) {
                return adgroup.has(stat) && adgroup.has('daily_stats');
            });
            if (adgroups.length === 0) {
                return [];
            }
            var sorted_adgroups = _.sortBy(adgroups, function(adgroup) {
                // dash because we're sorting in reverse order
                return -adgroup.get('impression_count');
            });
            var top_three_adgroups = sorted_adgroups.splice(0, 3);
            var other_adgroups = new AdGroups(sorted_adgroups);
            var chart_data = top_three_adgroups.map(function(adgroup) {
                var adgroup_data = {};
                adgroup_data[adgroup.get('name')] = _.map(adgroup.get('daily_stats'), function(day) {
                    return day[stat];
                });
                return adgroup_data;
            });
            if (other_adgroups.size()) {
                chart_data.push({
                    'Others': other_adgroups.get_total_daily_stats(stat)
                });
            }
            if (stat === 'ctr') {
                chart_data.push({
                    'MoPub Optimized': this.get_total_daily_stats('ctr')
                });
            }
            return chart_data;
        },

        get_days: function() {
            // TODO: make this less hacky
            return this.reduce(function(memo, adgroup) {
                return (adgroup.has('daily_stats') &&
                        adgroup.get('daily_stats').length > memo) ? adgroup.get('daily_stats').length : memo;
            }, 0);
        },

        isFullyLoaded: function() {
            // TODO: make this less hacky
            return this.reduce(function(memo, adgroup) {
                return memo && adgroup.has('impression_count');
            }, true);
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
            var app = response[0];
            console.log(app.app_type === 'iphone');
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
     * Globalize. We should find a better way to do this.
     */
    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;
    window.AdGroup = AdGroup;
    window.AdGroups = AdGroups;


}(this.jQuery, this.Backbone, this._));