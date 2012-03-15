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
    StatsError.prototype = Error.prorotype;
    

    /*
     * ### StatsMixin
     * Helpful utilities for fetching and formatting stats.
     */
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
            
            // For older servers, emulate HTTP by mimicking the HTTP method with `_method`
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
        },
        invalidations: function () {
            var stats_endpoint = this.get('stats_endpoint');
            // When we invalidate this model, we have to also
            // invalidate it's potential parent collection
            var collection_url = '/api/app/'
                + this.app_id
                + '/adunits/'
                + '?'
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
            return [ this.url(), collection_url ];
        }
    });

    _.extend(AdUnit.prototype, LocalStorageMixin);

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
        }, 
        invalidations: function() {
            var invalids = this.map(this.models, function(model) {
                return model.invalidations();
            });
            return _.flatten(invalids);
        },
        parse: function(response) {
            // We need to make sure each of the adunits knows which
            // stats endpoint we're using            
            var collection = this;
            var adunits = _.map(response, function(adunit){
                return _.extend(adunit, { stats_endpoint: collection.stats_endpoint });
            });
            return adunits;
        }
    });

    _.extend(AdUnitCollection.prototype, LocalStorageMixin);

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
        invalidations: function () {
            return [ this.url() ];
        }
    });

    _.extend(App.prototype, LocalStorageMixin);

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
        invalidations: function() {
            var invalids = this.map(this.models, function(model) {
                return model.invalidations();
            });
            return _.flatten(invalids);
        }
    });

    _.extend(AppCollection.prototype, LocalStorageMixin);

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

    _.extend(AdGroup.prototype, StatsMixin, LocalStorageMixin);

    var AdGroupCollection = Backbone.Collection.extend({
        model: AdGroup,
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/campaign/' 
                + this.campaign_id
                + "?"
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        },
        parse: function(response) {
            return response.adunits;
        }
    });


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

    _.extend(Campaign.prototype, StatsMixin, LocalStorageMixin);

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

    _.extend(CampaignCollection.prototype, LocalStorageMixin);

    /*
     * EXPOSE HIS JUNK
     * (We should find a better way to do this.)
     */
    // mopub.Models.AdUnit = AdUnit;
    // mopub.Models.AdUnitCollection = AdUnitCollection;
    // mopub.Models.App = App;
    // mopub.Models.AppCollection = AppCollection;
    // mopub.Models.AdGroup = AdGroup;
    // mopub.Models.AdGroupCollection = AdGroupCollection;
    // mopub.Models.Campaign = Campaign;
    // mopub.Models.CampaignCollection = CampaignCollection;

    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;
    window.AdGroup = AdGroup;
    window.AdGroupCollection = AdGroupCollection;
    window.Campaign = Campaign;
    window.CampaignCollection = CampaignCollection;


})(window.jQuery, window.Backbone, window._, window.mopub || { Models: {} });