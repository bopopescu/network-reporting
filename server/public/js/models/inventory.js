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
     * ## AdGroups
     */

    /*
     * Helper functions for stats
     */
    function calculate_ctr(imp, clk) {
        if (imp === null || clk === null || imp === undefined || clk === undefined) {
            return null;
        }
        return (imp === 0) ? 0 : clk / imp;
    }

    function calculate_fill_rate(req, imp) {
        if (req === null || imp === null || req === undefined || imp === undefined) {
            return null;
        }
        return (req === 0) ? 0 : imp / req;
    }

    function calculate_cpm(imp, rev) {
        if (imp === null || rev === null || imp === undefined || rev === undefined) {
            return null;
        }
        return (imp === 0) ? 0 : rev / imp * 1000;
    }

    function format_stat(stat, value) {
        if (value === null || value === undefined) {
            return '--';
        }
        switch (stat) {
          case 'att':
          case 'clk':
          case 'conv':
          case 'goal':
          case 'imp':
          case 'imp':
          case 'req':
          case 'att':
            return mopub.Utils.formatNumberWithCommas(value);
          case 'cpm':
          case 'rev':
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
    
    // Records an event in all of the metrics tracking services we
    // use.
    function record_metric (name, args) {
        try {
            _kmq.push(['record', name, args]);
        } catch (x) {
            console.log(x);
        }

        try {
            mixpanel.track(name, args);
        } catch (x) {
            console.log(x);
        }
    }

    
    var ModelHelpers = {
        calculate_ctr: calculate_ctr,
        calculate_fill_rate: calculate_fill_rate,
        format_stat: format_stat
    };


    /*
     * ## StatsModel
     */
    var StatsModel = Backbone.Model.extend({
        get_stat: function(stat) {
            switch(stat) {
                case 'ctr':
                    return calculate_ctr(this.get('imp'),
                                         this.get('clk'));
                case 'fill_rate':
                    return calculate_fill_rate(this.get('req'),
                                               this.get('imp'));
                case 'cpm':
                    return this.get(stat) || calculate_cpm(this.get('imp'),
                                                           this.get('rev'));
                case 'clk':
                case 'conv':
                case 'imp':
                case 'req':
                case 'att':
                case 'rev':
                case 'goal':
                case 'pace':
                case 'conv_rate':
                    return this.get(stat);
                default:
                    throw 'Unsupported stat "' + stat + '".';
            }
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

            if (!day_stats.hasOwnProperty(stat)) {
                return null;
            }
            return day_stats[stat];
        },
    });

    /*
     * ## StatsModels Collection
     */
    var StatsModels = Backbone.Collection.extend({
        model: StatsModel,

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
                    return calculate_ctr(this.get_stat('imp'),
                                         this.get_stat('clk'));
                case 'fill_rate':
                    return calculate_fill_rate(this.get_stat('req'),
                                               this.get_stat('imp'));
                case 'cpm':
                    return this.get(stat) || calculate_cpm(this.get_stat('imp'),
                                                           this.get_stat('rev'));
                case 'clk':
                case 'conv':
                case 'imp':
                case 'req':
                case 'att':
                case 'rev':
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
                    !(adgroup.get('daily_stats')[day]).hasOwnProperty(stat)) {
                    return null;
                }

                return memo + adgroup.get('daily_stats')[day][stat];
            }, 0);
        },

        get_stat_for_day: function(stat, day) {
            // TODO: Standardize field naming
            switch(stat) {
                case 'ctr':
                    return calculate_ctr(this.get_stat_for_day('imp', day),
                                         this.get_stat_for_day('clk', day));
                case 'fill_rate':
                    return calculate_fill_rate(this.get_stat_for_day('req', day),
                                               this.get_stat_for_day('imp', day));
                case 'cpm':
                    return calculate_cpm(this.get_stat_for_day('imp', day),
                                         this.get_stat_for_day('rev', day));
                case 'clk':
                case 'conv':
                case 'imp':
                case 'req':
                case 'att':
                case 'rev':
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

        get_formatted_total_daily_stats: function(stat) {
            var formatted_total_daily_stats = [];
            var day;
            for(day in this.at(0).get('daily_stats')) {
                formatted_total_daily_stats.push(this.get_formatted_stat_for_day(stat, day));
            }
            return formatted_total_daily_stats;
        },

        get_chart_data: function(stat, mopub_optimized) {
            var adgroups = this.filter(function(adgroup) {
                return adgroup.has(stat) && adgroup.has('daily_stats');
            });
            if (adgroups.length === 0) {
                return [];
            }
            var sorted_adgroups = _.sortBy(adgroups, function(adgroup) {
                // dash because we're sorting in reverse order
                return -adgroup.get('imp');
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
            if (stat === 'ctr' && mopub_optimized) {
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
                return memo && adgroup.has('imp');
            }, true);
        }
    });

    
    /*
     * ## Campaign Model
     */

    var Campaign = StatsModel.extend({
        defaults : {
            stats_endpoint: 'all'
        },
        url: function() {
            // window.location.search.substring(1) is used to preserve date ranges from the url
            // this makes the fetching work with the datepicker.
            var stats_endpoint = this.get('stats_endpoint');
            return '/api/campaign/'
                + this.id
                + '?'
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        },
        parse: function(response) {
            if (response) {
                var campaign_data = response.sum;
                campaign_data.daily_stats = response.daily_stats;

                // REFACTOR attempts vs requests
                if(campaign_data.req == null || campaign_data.req == undefined) {
                    campaign_data.req = campaign_data.att;
                } else if(campaign_data.att == null || campaign_data.att == undefined) {
                    campaign_data.att = campaign_data.req;
                } 

                return campaign_data;
            }
        }
    });


    /*
     * ## Campaigns Collection
     */
    var Campaigns = StatsModels.extend({
        model: Campaign,
    });


    /*
     * ## AdGroup model
     * This will most likely need to be refactored soon when we change how
     * AdGroups work on the backend.
     */

    var AdGroup = StatsModel.extend({
        url: function() {
            return '/api/adgroup/' + this.id;
        }
    });


    /*
     * ## Adgroup Collection
     */
    var AdGroups = StatsModels.extend({
        model: AdGroup,
    });


    /*
     * ## AdUnit
     */
    var AdUnit = StatsModel.extend({
        // If we don't set defaults, the templates will explode
        defaults : {
            active: false,
            att: 0,
            clk: 0,
            ctr: 0,
            cpm: 0,
            fill_rate: 0,
            imp: 0,
            name: '',
            price_floor: 0,
            requests: 0,
            rev: 0,
            stats_endpoint: 'all'
        },
        validate: function(attributes) {
            var current_price_floor = this.get('price_floor');
            if (typeof(attributes.price_floor) !== 'undefined') {
                var valid_number = Number(attributes.price_floor);
                if (isNaN(valid_number)) {
                    return "Please enter a valid number for the price floor";
                } else {
                    if (current_price_floor !== valid_number) {
                        record_metric('MPX Price Floor Changed', {
                            'from': current_price_floor,
                            'to': valid_number
                        });
                    }
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
            if (this.campaign_id) {
                return '/api/campaign/'
                    + this.campaign_id
                    + '/adunits/'
                    + '?'
                    + window.location.search.substring(1)
                    + '&endpoint='
                    + this.stats_endpoint;
            } else {
                return '/api/app/'
                    + this.app_id
                    + '/adunits/'
                    + '?'
                    + window.location.search.substring(1)
                    + '&endpoint='
                    + this.stats_endpoint;
            }
        },

        parse: function(response) {
            // REFACTOR attempts vs requests
            _.each(response, function(adunit) {
                if(adunit.req == null || adunit.req == undefined) {
                    adunit.req = adunit.att;
                } else if (adunit.att == null || adunit.att == undefined) {
                    adunit.att = adunit.req;
                }
            });

            return response;
        },

        isFullyLoaded: function() {
            // TODO: make this less hacky
            return this.reduce(function(memo, adunit) {
                return memo && adunit.has('imp');
            }, true);
        }
    });


    /*
     * ## App
     * We might consider turning derivative values (cpm, fill_rate, ctr) into
     * functions.
     */
    var App = StatsModel.extend({
        defaults : {
            name: '',
            url:'#',
            icon_url: "/placeholders/image.gif",
            app_type: '',
            active: false,
            att: 0,
            clk: 0,
            ctr: 0,
            cpm: 0,
            fill_rate: 0,
            imp: 0,
            price_floor: 0,
            requests: 0,
            rev: 0,
            status: 'Running',
            stats_endpoint: 'all'
        },
        url: function () {
            var stats_endpoint = this.get('stats_endpoint');
            if (this.get('campaign_id')) {
                return '/api/campaign/'
                    + this.get('campaign_id')
                    + '/apps/'
                    + this.id
                    + "?"
                    + window.location.search.substring(1)
                    + '&endpoint='
                    + stats_endpoint;
            } else {
                return '/api/app/'
                    + this.id
                    + "?"
                    + window.location.search.substring(1)
                    + '&endpoint='
                    + stats_endpoint;
            }
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            var app = response[0];

            // REFACTOR attempts vs requests
            if(app.req == null || app.req == undefined) {
                app.req = app.att;
            } else if (app.att == null || app.att == undefined) {
                app.att = app.req;
            }

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
     * EXPOSE HIS JUNK
     * (We should find a better way to do this.)
     */
    window.StatsModel = StatsModel;
    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;
    window.AdGroup = AdGroup;
    window.AdGroups = AdGroups;
    window.Campaign = Campaign;
    window.Campaigns = Campaigns;
    window.ModelHelpers = ModelHelpers;


}(this.jQuery, this.Backbone, this._));
