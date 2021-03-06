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

    // Gets the url from a backbone model/collection.
    // Sometimes it's a string, sometimes its a function.
    // This is used as utility for localStorage caching,
    // but could be used for anything.
    var getUrl = function(object) {
        if (!(object && object.url)) return null;
        return _.isFunction(object.url) ? object.url() : object.url;
    };

    /*
     * ### UrlError
     * Throw this when you try to fetch a model and it has an
     * undefined or invalid url.
     */
    function UrlError(message) {
        this.name = "UrlError";
        this.message = message || "";
    }
    UrlError.prototype = Error.prototype;

    /*
     * ### StatsError
     * Throw this when a model's stat property doesn't exist or we
     * don't know how to format it.
     */
    function StatsError(message) {
        this.name = "StatsError";
        this.message = message || "";
    }
    StatsError.prototype = Error.prototype;

    /*
     * Helper functions for stats
     */
    function calculate_ctr(imp, clk) {
        if (imp === null || clk === null || imp === undefined || clk === undefined) {
            return null;
        }
        return (imp === 0) ? 0 : (clk / imp);
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

    function calculate_conv_rate(conv, clk) {
        if (conv === null || clk === null || conv === undefined || clk === undefined) {
            return null;
        }

        return (clk === 0) ? 0 : conv / clk;
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
            value = value * 100;
            if(value > 250) {
                return '>250%';
            }
            return value.toFixed() + '%';
        default:
            throw 'Unsupported stat "' + stat + '".';
        }
    }

    // Records an event in all of the metrics tracking services we
    // use.
    function record_metric (name, args) {
        try {
            //mixpanel.track(name, args);
        } catch (x) {
            console.log(x);
        }
    }

    /*
     * ### StatsMixin
     * Helpful utilities for fetching and formatting stats.
     */
    var StatsMixin = {

        /*
         * `get_stat`
         * Gets the raw stat value from a model. Calculates
         * derivative (fill_rate/ctr/cpm/conv_rate) stats from
         * other raw stats.
         *
         * Works for models only.
         */
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
                case 'conv_rate':
                    return this.get(stat) || calculate_conv_rate(this.get_stat('conv'),
                                                                 this.get_stat('clk'));
                case 'clk':
                case 'conv':
                case 'imp':
                case 'req':
                case 'att':
                case 'rev':
                    var stat_val = this.get("sum")[stat];
                    if (stat_val) {
                        return stat_val;
                    } else {
                        return 0;
                    }
                default:
                    throw 'Unsupported stat "' + stat + '".';
            }
        },

        get_formatted_stat: function(stat) {
            return format_stat(stat, this.get_stat(stat));
        },


        /*
         * `get_formatted_stat_sum`
         * Returns the summed (or averaged, for some derivative stats)
         * stat total, and formats it accordingly.
         *
         * e.g. get_formatted_stat_sum('rev')  // "$1,402.53"
         *
         * Works for collections.
         */
        get_formatted_stat_sum: function(stat) {
            var these_models = this.models;

            if (stat === 'ctr') {

                var imp_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('imp');
                }, 0);
                var clk_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('clk');
                }, 0);
                var total_ctr = calculate_ctr(imp_sum, clk_sum);

                return format_stat('ctr', total_ctr);

            } else if (stat === 'fill_rate') {

                var req_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('req');
                }, 0);
                var imp_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('imp');
                }, 0);
                var total_fill_rate = calculate_fill_rate(req_sum, imp_sum);

                return format_stat('fill_rate', total_fill_rate);

            } else if (stat === 'conv_rate') {

                var conv_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('conv');
                }, 0);
                var clk_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('clk');
                }, 0);
                var total_conv_rate = calculate_conv_rate(conv_sum, clk_sum);

                return format_stat('conv_rate', total_conv_rate);

            } else if (stat === 'cpm') {

                var imp_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('imp');
                }, 0);
                var rev_sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat('rev');
                }, 0);
                var total_cpm = calculate_cpm(imp_sum, rev_sum);

                return format_stat('cpm', total_cpm);

            } else {
                var sum = these_models.reduce(function(memo, model){
                    return memo + model.get_stat(stat);
                }, 0);

                return format_stat(stat, sum);
            }
        },



        /*
         * `get_formatted_daily_stats`
         * Returns an object with formatted stats for each day
         * in daily_stats. So, if daily_stats contains 14 days
         * of data, this will return an object like this:
         *
         * {
         *    clk: "0",
         *    conv: "0",
         *    conv_rate: "0.00%",
         *    cpm: "$0.00",
         *    ctr: "0.00%",
         *    date: "Thursday, Jun 7, 2012",
         *    fill_rate: "0.00%",
         *    imp: "0",
         *    req: "0",
         *    rev: "$0.00",
         * }
         *
         * for each of the 14 days.
         *
         * Works for models only (not for collections).
         */
        get_formatted_daily_stats: function () {
            return _.map(this.get('daily_stats'), function (day) {

                // Calculate derivative values
                day.fill_rate = calculate_fill_rate(day.req, day.imp);
                day.ctr = calculate_ctr(day.imp, day.clk);
                day.cpm = calculate_cpm(day.imp, day.rev);
                day.conv = day.conv || 0;
                day.conv_rate = calculate_conv_rate(day.conv, day.clk);

                // Format each of them
                _.each(_.keys(day), function (key) {
                    if (key !== 'date') {
                        day[key] = format_stat(key, day[key]);
                    } else {
                        day[key] = moment(day[key], "YYYY-MM-DD").format("dddd, MMM D, YYYY");
                    }
                });

                return day;
            });
        },

        /*
         * `get_formatted_stat_series`
         * For each model in a collection, and for each day in each model's
         * daily_stats, returns the raw value for the stat. Useful for
         * putting together graphs.
         */
        get_full_stat_series: function(stat) {

            var models_in_collection = this.models.length;

            if (stat === "ctr") {
                var imp_series = this.get_full_stat_series('imp');
                var clk_series = this.get_full_stat_series('clk');

                var ctr_series = [];
                _.each(_.zip(imp_series, clk_series), function (pair) {
                    ctr_series.push(calculate_ctr(pair[0], pair[1]));
                });

                return ctr_series;
            } else if (stat === "cpm") {
                var imp_series = this.get_full_stat_series('imp');
                var rev_series = this.get_full_stat_series('rev');

                var cpm_series = [];
                _.each(_.zip(imp_series, rev_series), function (pair) {
                    cpm_series.push(calculate_cpm(pair[0], pair[1]));
                });

                return cpm_series;

            } else {

                // Go through each of the daily stats for each of the
                // models in the collection and pull them out.
                // At the end of this we'll have an array of arrays, where
                // each inner array has the daily values for the particular stat,
                // one inner array per model
                var dailies_for_stat = this.map(function(model) {
                    var daily_stats = model.get('daily_stats');
                    return _.map(daily_stats, function (day) {
                        return day[stat];
                    });
                });

                // Now sum by day
                var memo = [];
                _.times(dailies_for_stat[0].length, function (t) { memo.push(0); });

                // Turn this 2D Array into a 1D array
                var full_series = _.reduce(dailies_for_stat, function (memo, day_stats){
                    _.times(memo.length, function (iter){
                        memo[iter] += day_stats[iter];
                    });

                    return memo;
                }, memo);

                return full_series;
            }
        },

        get_date_range: function() {
            var dailies = this.models[0].get('daily_stats');

            return _.map(dailies, function (day) {
                var date = moment(day.date);
                return date.unix();
            });
        },

        get_epoch_date_range: function () {

        }
    };


    /*
     * ### LocalStorageMixin
     * If the browser has localstorage, then use it to cache model/collection
     * properties. If cached properties are found in localstorage, load them
     * and then perform the sync over ajax to make sure we have the most up
     * to date data.
     *
     * This will *always* sync over ajax to make sure we have the most up to
     * date data.
     */
    var LocalStorageMixin = {
        sync: function (method, model, options) {

            // Map of backbone methods to their HTTP equivalent,
            // for utility purposes
            var methodMap = {
                create: 'POST',
                update: 'PUT',
                delete: 'DELETE',
                read: 'GET'
            };

            // Taken from Modernizr. Determines if we have
            // localstorage or not.
            function supports_local_storage() {
                try {
                    return 'localStorage' in window && window.localStorage !== null;
                } catch (e) {
                    return false;
                }
            }

            var type = methodMap[method];

            // Default JSON-request options.
            var params = _.extend({
                type: type,
                dataType: 'json'
            }, options);

            // Ensure that we have a URL.
            if (!params.url) {
                params.url = getUrl(model);
                if (params.url === undefined) {
                    throw new UrlError('Unable to retrieve a valid url from model');
                }
            }

            // Ensure that we have the appropriate request data.
            if (!params.data && model && (method == 'create' || method == 'update')) {
                params.contentType = 'application/json';
                params.data = JSON.stringify(model.toJSON());
            }

            // For older servers, emulate JSON by encoding the request into an HTML-form.
            if (Backbone.emulateJSON) {
                params.contentType = 'application/x-www-form-urlencoded';
                params.data = params.data ? {model : params.data} : {};
            }

            // For older servers, emulate HTTP by mimicking the HTTP method
            // with `_method`

            // And an `X-HTTP-Method-Override` header.
            if (Backbone.emulateHTTP) {
                if (type === 'PUT' || type === 'DELETE') {
                if (Backbone.emulateJSON) params.data._method = type;
                    params.type = 'POST';
                    params.beforeSend = function(xhr) {
                        xhr.setRequestHeader('X-HTTP-Method-Override', type);
                    };
                }
            }

            // Don't process data on a non-GET request.
            if (params.type !== 'GET' && !Backbone.emulateJSON) {
                params.processData = false;
            }

            // This is the modified part:
            // - Look for the cached version and trigger success if it's present.
            // - Modify the AJAX request so it'll save the data on success.
            if (method === 'read' && supports_local_storage()) {

                var key = "mopub-cache/" + params.url;

                // Look for the cached version
                var val = localStorage.getItem(key);
                var success_function = params.success;

                // If we have the last response cached, use it with
                // the success callback
                if (val) {
                    _.defer(function () {
                        success_function(JSON.parse(val), "success");
                    });
                }

                // Overwrite the success callback to save data to localStorage
                params.success = function (resp, status, xhr) {
                    success_function(resp, status, xhr);
                    localStorage.removeItem(key);
                    localStorage.setItem(key, xhr.responseText);
                };

            } else if (method === 'update' || method === 'delete') {
                // If we're updating or deleting the model, invalidate
                // everything associated with it. If the model doesn't
                // have an invalidations method, we can just use the
                // url.
                var invalidations = model.invalidations() || [ params.url ];
                _.each(invalidations, function(invalidation_key){
                    var key = "mopub-cache/" + invalidation_key;
                    localStorage.removeItem(key);
                });

            }

            // Make the request.
            return $.ajax(params);
        }
    };


    var ModelHelpers = {
        calculate_ctr: calculate_ctr,
        calculate_fill_rate: calculate_fill_rate,
        calculate_conv_rate: calculate_conv_rate,
        format_stat: format_stat
    };


    /*
     * ## StatsModel
     */
    var StatsModel = Backbone.Model.extend({
        get_stat: function(stat) {
            switch(stat) {
                case 'ctr':
                    return calculate_ctr(this.get_stat('imp'),
                                         this.get_stat('clk'));
                case 'fill_rate':
                    return calculate_fill_rate(this.get_stat('req'),
                                               this.get_stat('imp'));
                case 'conv_rate':
                    return calculate_conv_rate(this.get_stat('conv'),
                                               this.get_stat('clk'));
                case 'cpm':
                    return this.get(stat) || calculate_cpm(this.get_stat('imp'),
                                                           this.get_stat('rev'));
                case 'clk':
                case 'conv':
                case 'imp':
                case 'req':
                case 'att':
                case 'rev':
                case 'goal':
                case 'pace':
                    var stat_val;
                    try {
                        stat_val = this.get("sum")[stat];
                    } catch (e) {
                        stat_val = this.get(stat);
                    }

                    if (stat_val){
                        return stat_val;
                    } else {
                        return 0;
                    }

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
        }
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
        defaults: {
            app: null,
            adunit: null,
            include_daily: false,
            include_adgroups: false,
            include_creatives: false,
            start_date: null,
            date_range: 90,
            stats_endpoint: 'all'
        },
        url: function () {
            var url = '/api/campaign/' + this.id + '?';
            var app = this.get('app');
            var date_range = this.get('date_range');
            if (date_range <= 0) {
                date_range = 1;
            }
            if(app) {
                url += '&app=' + app;
            }
            else {
                var adunit = this.get('adunit');
                if(adunit) {
                    url += '&adunit=' + adunit;
                }
            }
            url += '&daily=' + (this.get('include_daily') ? '1' : '0');
            url += '&adgroups=' + (this.get('include_adgroups') ? '1' : '0');
            url += '&creatives=' + (this.get('include_creatives') ? '1' : '0');
            var start_date = this.get('start_date');
            if(start_date) {
                url += '&s=' + start_date.getFullYear() + '-' + (start_date.getMonth() + 1) + '-' + start_date.getDate();
            }
            url += '&r=' + date_range;
            url += '&endpoint=' + this.get('stats_endpoint');
            return url;
        },
        parse: function(response) {
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
            conv: 0,
            fill_rate: 0,
            imp: 0,
            name: '',
            price_floor: 0,
            req: 0,
            rev: 0,
            stats_endpoint: 'all',
            start_date: null,
            date_range: 90
        },
        validate: function(attributes) {

            var current_price_floor = this.get('price_floor');
            if (typeof(attributes.price_floor) !== 'undefined') {
                var valid_number = Number(attributes.price_floor);
                if (isNaN(valid_number)) {
                    return "Please enter a valid number for the price floor";
                } else if (valid_number < 0) {
                    return "Please enter a non-negative number for the price floor";
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
        url: function () {
            var url = '/api/app/' + this.get('app_id') + '/adunits/' + this.id + '?';
            var start_date = this.get('start_date');
            if(start_date) {
                url += '&s=' + start_date.getFullYear() + '-' + (start_date.getMonth() + 1) + '-' + start_date.getDate();
            }
            url += '&r=' + this.get('date_range');
            url += '&endpoint=' + this.get('stats_endpoint');
            return url;
        },
        parse: function(response) {
            for(var i in response) {
                if(response[i].id === this.id) {
                    return response[i];
                }
            }
            return null;
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
            var collection = this;
            // REFACTOR attempts vs requests
            _.each(response, function(adunit) {

                if(adunit.hasOwnProperty('sum')) {
                    if (adunit.sum.hasOwnProperty('req') && adunit.sum.req !== null && !adunit.sum.hasOwnProperty('att')) {
                        adunit.sum.att = adunit.sum.req;
                    }
                    else if (adunit.sum.hasOwnProperty('att') && adunit.sum.att !== null && !adunit.sum.hasOwnProperty('req')) {
                        adunit.sum.req = adunit.sum.att;
                    }
                }
                else {
                    if (adunit.hasOwnProperty('req') && adunit.req !== null && !adunit.hasOwnProperty('att')) {
                        adunit.att = adunit.req;
                    }
                    else if (adunit.hasOwnProperty('att') && adunit.att !== null && !adunit.hasOwnProperty('req')) {
                        adunit.req = adunit.att;
                    }
                }

                _.extend(adunit, { stats_endpoint: collection.stats_endpoint });
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
            conv: 0,
            fill_rate: 0,
            imp: 0,
            price_floor: 0,
            req: 0,
            rev: 0,
            status: 'Running',
            stats_endpoint: 'all',
            start_date: null,
            date_range: 90
        },
        url: function () {
            var url = '/api/';
            if (this.get('campaign_id')) {
                url += 'campaign/' + this.get('campaign_id') + '/apps/';
            } else {
                url += 'app/';
            }
            url += this.id + '?';
            var start_date = this.get('start_date');
            if(start_date) {
                url += '&s=' + start_date.getFullYear() + '-' + (start_date.getMonth() + 1) + '-' + start_date.getDate();
            }
            url += '&r=' + this.get('date_range');
            url += '&endpoint=' + this.get('stats_endpoint');
            return url;
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            var app = response[0];

            // REFACTOR attempts vs requests
            if((app.req === null || app.req === undefined) &&
               (app.att !== null && app.att !== undefined)) {
                app.req = app.att;
            } else if ((app.att == null || app.att == undefined) &&
                       (app.rev !== null && app.rev !== undefined)) {
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

    _.extend(App.prototype, StatsMixin);

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

    _.extend(AppCollection.prototype, StatsMixin);


    /*
     *  Order
     */
    var Order = Backbone.Model.extend({
        defaults: {
            app: null,
            adunit: null,
            include_daily: false,
            include_adgroups: false,
            include_creatives: false,
            start_date: null,
            date_range: 90
        },
        url: function () {
            var url = '/api/campaign/' + this.id + '?';
            var app = this.get('app');
            var date_range = this.get('date_range');
            if (app) {
                url += '&app=' + app;
            } else {
                var adunit = this.get('adunit');
                if(adunit) {
                    url += '&adunit=' + adunit;
                }
            }

            if (date_range <= 0) {
                date_range = 1;
            }

            url += '&daily=' + (this.get('include_daily') ? '1' : '0');
            url += '&adgroups=' + (this.get('include_adgroups') ? '1' : '0');
            url += '&creatives=' + (this.get('include_creatives') ? '1' : '0');
            var start_date = this.get('start_date');
            if(start_date) {
                url += '&s=' + start_date.getFullYear() + '-' + (start_date.getMonth() + 1) + '-' + start_date.getDate();
            }
            url += '&r=' + date_range;
            return url;
        },
        parse: function(order) {
            // TODO: this throws an error if req is undefined
            if((order.req === null || order.req === undefined) &&
               (order.att !== null && order.att !== undefined)) {
                order.req = order.att;
            } else if ((order.att == null || order.att == undefined) &&
                       (order.rev !== null && order.rev !== undefined)) {
                order.att = order.req;
            }
            return order;
        }
    });

    _.extend(Order.prototype, StatsMixin);


    var OrderCollection = Backbone.Collection.extend({
        model: Order
    });

    _.extend(OrderCollection.prototype, StatsMixin);


    /*
     *  LineItem
     */
    var LineItem = Backbone.Model.extend({
        defaults: {
            app: null,
            adunit: null,
            include_daily: false,
            include_creatives: false,
            start_date: null,
            date_range: 90,
            // TODO: Why do we need all these defaults?  It seems like it will
            // hide legitimate errors if stats don't load.
            name: '',
            att: 0,
            clk: 0,
            ctr: 0,
            cpm: 0,
            conv: 0,
            fill_rate: 0,
            imp: 0,
            req: 0,
            rev: 0,
            allocation: null,
            frequency_caps: null,
            country_targeting: null,
            device_targeting: []
        },
        url: function () {
            var url = '/api/adgroup/' + this.id + '?';
            var app = this.get('app');
            if(app) {
                url += '&app=' + app;
            }
            else {
                var adunit = this.get('adunit');
                if(adunit) {
                    url += '&adunit=' + adunit;
                }
            }
            url += '&daily=' + (this.get('include_daily') ? '1' : '0');
            url += '&creatives=' + (this.get('include_creatives') ? '1' : '0');
            var start_date = this.get('start_date');
            if(start_date) {
                url += '&s=' + start_date.getFullYear() + '-' + (start_date.getMonth() + 1) + '-' + start_date.getDate();
            }
            url += '&r=' + this.get('date_range');
            return url;
        }
    });

    _.extend(LineItem.prototype, StatsMixin);


    var LineItemCollection = Backbone.Collection.extend({
        model: LineItem,
        stats_endpoint: 'direct',
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/campaign/'
                + this.campaign_id
                + "?r=90"
                + '&endpoint='
                + stats_endpoint;
        },
        parse: function(response) {
            return response.adunits;
        }
    });

    _.extend(LineItemCollection.prototype, StatsMixin);


    /*
     *  Creative
     */
    var Creative = Backbone.Model.extend({
        defaults: {
            start_date: null,
            date_range: 90,
            name: '',
            att: 0,
            clk: 0,
            ctr: 0,
            cpm: 0,
            conv: 0,
            fill_rate: 0,
            imp: 0,
            req: 0,
            rev: 0
        },
        url: function () {
            var url = '/api/creative/' + this.id + '?';
            var start_date = this.get('start_date');
            if(start_date) {
                url += 's=' + start_date.getFullYear() + '-' + (start_date.getMonth() + 1) + '-' + start_date.getDate();
            }
            url += '&r=' + this.get('date_range');
            url += '&endpoint=direct';
            return url;
        }
    });

    _.extend(Creative.prototype, StatsMixin);


    var CreativeCollection = Backbone.Collection.extend({
        model: Creative,
        // url: function() {
        //     var stats_endpoint = this.stats_endpoint;
        //     return '/api/campaign/'
        //         + this.campaign_id
        //         + "?r=90"
        //         + '&endpoint='
        //         + stats_endpoint;
        // },
        // parse: function(response) {
        //     return response.adunits;
        // }
    });

    _.extend(CreativeCollection.prototype, StatsMixin);


    /*
     * EXPOSE THIS JUNK
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

    window.StatsMixin = StatsMixin;

    window.Order = Order;
    window.LineItem = LineItem;
    window.Creative = Creative;
    window.OrderCollection = OrderCollection;
    window.LineItemCollection = LineItemCollection;
    window.CreativeCollection = CreativeCollection;

} (this.jQuery, this.Backbone, this._));
