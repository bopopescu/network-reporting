/*
 * # views.js
 * Reusable UI elements written with Backbone.
 */

/*jslint browser:true,
  fragment: true,
  maxlen: 110,
  nomen: true,
  indent: 4,
  vars: true,
  white: true
 */

var mopub = window.mopub || {};

(function ($, Backbone, _) {
    "use strict";
    /*
     * ## CampaignView
     * Parameters:
     * * model: Campaign
     */
    var CampaignView = Backbone.View.extend({
        initialize: function () {
            this.model.bind('change', this.render, this);
        },
        render: function () {
            var metrics = ['att', 'imp', 'fill_rate', 'clk', 'ctr'];
            var this_view = this;
            var row = $("tr#" + this_view.model.id + "-row");

            if (this_view.model.get('stats_endpoint') == 'networks') {
                var selector = ' .network-data';

                $('.rev', row).text(this_view.model.get_formatted_stat('rev'));
                $('.cpm' + selector, row).text(this_view.model.get_formatted_stat('cpm'));
            } else {
                var selector = ' .mopub-data';
            }

            _.each(metrics, function (metric) {
                var stat = this_view.model.get_stat(metric);
                if (stat || stat == 0) {
                    $('.' + metric + selector, row).text(this_view.model.get_formatted_stat(metric));
                }
            });

            return this;
        }
    });

    
    /*
     * ## AdGroupsView
     * Parameters:
     * * collection: AdGroups
     * * el: element that will hold the content
     * * title: title that will be an h2 at the top of the content
     * * type: 'network', 'gtee', 'promo', or 'backfill_promo' -- affects which fields are shown
     * * tables: mapping of... MAPPING OF WHAT? I'M DYING TO KNOW
     */
    var AdGroupsView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },
        filtered_collection: function () {
            // TODO: uses elements not in this view
            var status = $('#campaigns-filterOptions').find(':checked').val();
            var app = $('#campaigns-appFilterOptions').val();
            return new AdGroups(this.collection.reject(function (adgroup) {
                return (status && status !== adgroup.get('status')) ||
                       (app && adgroup.get('apps').indexOf(app) === -1);
            }));
        },
        render: function () {
            var adgroups = this.filtered_collection();

            // TODO: uses elements not in this view, with multiple views there are conflicts

            var html;
            if (adgroups.size() === 0) {
                html = '<h2>No ' + this.options.title + '</h2>';
            } else {
                html = _.template($('#adgroups-rollup-template').html(), {
                    adgroups: adgroups,
                    title: this.options.title,
                    type: this.options.type
                });

                if (this.options.tables) {
                    var type = this.options.type;
                    _.each(this.options.tables, function (filter, title) {
                        var filtered_adgroups = new AdGroups(adgroups.filter(filter));
                        if(filtered_adgroups.length) {
                            html += _.template($('#adgroups-table-template').html(), {
                                adgroups: filtered_adgroups,
                                title: title,
                                type: type
                            });
                        }
                    });
                } else {
                    html += _.template($('#adgroups-table-template').html(), {
                        adgroups: adgroups,
                        title: 'Name',
                        type: this.options.type
                    });
                }
            }
            $(this.el).html(html);
            return this;
        }
    });

    var NetworkAdGroupsView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },
        filtered_collection: function () {
            // TODO: uses elements not in this view
            var status = $('#campaigns-filterOptions').find(':checked').val();
            var app = $('#campaigns-appFilterOptions').val();
            return new AdGroups(this.collection.reject(function (adgroup) {
                return (status && status !== adgroup.get('status')) ||
                       (app && adgroup.get('apps').indexOf(app) === -1);
            }));
        },
        render: function () {
            var adgroups = this.filtered_collection();

            // TODO: uses elements not in this view, with multiple views there are conflicts

            var html;
            if (adgroups.size() === 0) {
                html = '<h2>No ' + this.options.title + '</h2>';
            } else {
                html = _.template($('#adgroups-rollup-template').html(), {
                    adgroups: adgroups,
                    title: this.options.title,
                    type: this.options.type
                });

                if (this.options.tables) {
                    var type = this.options.type;
                    _.each(this.options.tables, function (filter, title) {
                        var filtered_adgroups = new AdGroups(adgroups.filter(filter));
                        if(filtered_adgroups.length) {
                            html += _.template($('#adgroups-table-template').html(), {
                                adgroups: filtered_adgroups,
                                title: title,
                                type: type
                            });
                        }
                    });
                } else {
                    html += _.template($('#adgroups-table-template').html(), {
                        adgroups: adgroups,
                        title: 'Name',
                        type: this.options.type
                    });
                }
            }
            $(this.el).html(html);
            return this;
        }
    });



    /*
     * # CollectionGraphView
     * Renders a collection as a graph
     */

    var CollectionGraphView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },

        show_chart: function () {
            var this_view = this;
            if(this.collection.isFullyLoaded()) {
                var active_chart = $('#dashboard-stats .stats-breakdown .active');
                var use_ctr = active_chart.attr('id') === 'stats-breakdown-ctr';
                mopub.Chart.setupDashboardStatsChart((use_ctr || this_view.options.line_graph) ? 'line' : 'area');
                $('#dashboard-stats-chart').show();
            }
        },

        render: function () {
            var this_view = this;
            if (this_view.collection.isFullyLoaded()) {

                var metrics = ['imp', 'rev', 'clk', 'ctr'];

                // Render the stats breakdown for "all""
                $.each(metrics, function (iter, metric) {
                    var selector = '#stats-breakdown-' + metric + ' .all .inner';
                    $(selector).html(this_view.collection.get_formatted_stat(metric));
                });

                if (this_view.options.yesterday !== null && this_view.options.today !== null) {

                    // Render the stats breakdown for yesterday
                    $.each(metrics, function (iter, metric) {
                        var selector = '#stats-breakdown-' + metric + ' .yesterday .inner';
                        $(selector).html(this_view.collection.get_formatted_stat_for_day(metric,
                                         this_view.options.yesterday));
                    });

                    // Render the stats breakdown for yesterday
                    $.each(metrics, function (iter, metric) {
                        var selector = '#stats-breakdown-' + metric + ' .today .inner';
                        $(selector).html(this_view.collection.get_formatted_stat_for_day(metric,
                                         this_view.options.today));
                    });
                }

                // Chart
                mopub.dashboardStatsChartData = {
                    pointStart: this_view.options.start_date,
                    pointInterval: 86400000,
                    imp: this_view.collection.get_chart_data('imp', this_view.options.mopub_optimized),
                    rev: this_view.collection.get_chart_data('rev', this_view.options.mopub_optimized),
                    clk: this_view.collection.get_chart_data('clk', this_view.options.mopub_optimized),
                    ctr: this_view.collection.get_chart_data('ctr', this_view.options.mopub_optimized),
                    total: false
                };
                this.show_chart();
            }
        }
    });

    var NetworkGraphView = CollectionGraphView.extend({
        render: function () {
            var this_view = this;

            if (this_view.collection.isFullyLoaded()) {
                var metrics = ['rev', 'imp', 'clk', 'ctr'];

                var network_campaigns = new Campaigns(_.filter(this.collection.models,
                    function(campaign){
                        return campaign.get('stats_endpoint') == 'networks';
                        }));;
                var mopub_campaigns = new Campaigns(_.filter(this.collection.models,
                    function(campaign){
                        return campaign.get('stats_endpoint') == 'all';
                        }));

                // Render the stats breakdown for each metric
                _.each(metrics, function (metric) {
                    var selector = '#stats-breakdown-' + metric;
                    // Mopub doesn't track rev
                    if (metric == 'rev') {
                        var mopub_selector = null;
                        var network_selector = selector + ' .network-chart-rev';
                    } else {
                        var mopub_selector = selector + ' .mopub-chart-data';
                        var network_selector = selector + ' .network-chart-data';
                    }
                    $(mopub_selector).html(mopub_campaigns.get_formatted_stat(metric));
                    $(network_selector).html(network_campaigns.get_formatted_stat(metric));
                });

                // Chart
                if (_.isEmpty(network_campaigns.models)) {
                    mopub.dashboardStatsChartData = {
                        pointStart: this_view.options.start_date,
                        pointInterval: 86400000,
                        imp: [{'Total': mopub_campaigns.get_total_daily_stats('imp')}],
                        clk: [{'Total': mopub_campaigns.get_total_daily_stats('clk')}],
                        ctr: [{'Total': mopub_campaigns.get_total_daily_stats('ctr')}],
                        total: false
                    };
                } else {
                    mopub.dashboardStatsChartData = {
                        pointStart: this_view.options.start_date,
                        pointInterval: 86400000,
                        imp: [{'From MoPub': mopub_campaigns.get_total_daily_stats('imp')}, {'From Networks': network_campaigns.get_total_daily_stats('imp')}],
                        rev: [{'From Networks': {'data': network_campaigns.get_total_daily_stats('rev'), 'color': '#e57300'}}],
                        clk: [{'From MoPub': mopub_campaigns.get_total_daily_stats('clk')}, {'From Networks': network_campaigns.get_total_daily_stats('clk')}],
                        ctr: [{'From MoPub': mopub_campaigns.get_total_daily_stats('ctr')}, {'From Networks': network_campaigns.get_total_daily_stats('ctr')}],
                        total: false
                    };
                }
                mopub.Chart.setupDashboardStatsChart('line');
                $('#dashboard-stats-chart').show();
            }
        }
    });


    var NetworkDailyCountsView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },

        render: function () {
            var this_view = this;

            if (this_view.collection.isFullyLoaded()) {
                var metrics = ['rev', 'cpm', 'imp', 'clk', 'ctr'];

                var network_campaigns = new Campaigns(_.filter(this.collection.models,
                    function(campaign){
                        return campaign.get('stats_endpoint') == 'networks';
                        }));;
                var mopub_campaigns = new Campaigns(_.filter(this.collection.models,
                    function(campaign){
                        return campaign.get('stats_endpoint') == 'all';
                        }));

                // Render Total daily count stats
                _.each(metrics, function (metric) {
                    var selector = '#dailyCounts-totals';
                    // Mopub doesn't track rev
                    if (metric == 'rev' || metric == 'cpm') {
                        var mopub_selector = null;
                        var network_selector = selector + ' .' + metric;
                    } else {
                        var mopub_selector = selector + ' .' + metric + ' .mopub-data';
                        var network_selector = selector + ' .' + metric + ' .network-data';
                    }
                    $(mopub_selector).text(mopub_campaigns.get_formatted_stat(metric));
                    if (!_.isEmpty(network_campaigns.models)) {
                        $(network_selector).text(network_campaigns.get_formatted_stat(metric));
                    }

                    function renderColumn(campaigns, selector) {
                        var totals = campaigns.get_formatted_total_daily_stats(metric).reverse();
                        // Render td in rows a column at a time
                        $('.dailyCounts-stats').each(function (index, row) {
                            var value = totals[index];
                            if (metric == 'rev' || metric == 'cpm') {
                                $(row).find('.' + metric).text(value);
                            } else {
                                $(row).find('.' + metric + selector).text(value);
                            }
                        });
                    }
                    renderColumn(mopub_campaigns, ' .mopub-data');
                    if (!_.isEmpty(network_campaigns.models)) {
                        renderColumn(network_campaigns, ' .network-data');
                    }
                });

            }
        }
    });


    /*
     * ## AppView
     *
     * See templates/partials/app.html to see how this is rendered in HTML.
     * This renders an app as a table row. It also adds the call to load
     * adunits over ajax and put them in the table.
     */
    var AppView = Backbone.View.extend({
        initialize: function () {
            if (this.options.endpoint_specific) {
                this.model.bind('change', this.render, this);
            }
            try {
                this.template = _.template($('#app-template').html());
            } catch (e) {
                // the template wasn't specified. this is ok if you
                // intend to renderInline
            }
        },

        renderInline: function () {
            var this_view = this;
            // Will there be multiple stats endpoints in this app row?
            if (this_view.options.endpoint_specific) {
                if (this_view.model.get('stats_endpoint') == 'networks') {
                    var selector = ' .network-data';
                } else {
                    var selector = ' .mopub-data';
                }
            } else {
                var selector = ''
            }
            var app_row = $('tr.app-row#app-' + this_view.model.id, this_view.el);

            /*jslint maxlen: 200 */
            if (!this_view.options.endpoint_specific || this_view.model.get('stats_endpoint') == 'networks') {
                $('.rev', app_row).text(this_view.model.get_formatted_stat('rev'));
                $('.cpm', app_row).text(this_view.model.get_formatted_stat('cpm'));
            }
            var metrics = ['imp', 'clk', 'ctr', 'fill_rate', 'req', 'att', 'conv', 'conv_rate'];
            _.each(metrics, function (metric) {
                $('.' + metric + selector, app_row).text(this_view.model.get_formatted_stat(metric));
            });
            /*jslint maxlen: 110 */

            $(".loading-img", app_row).hide();

            return this;
        },
        render: function () {
            if(!this.template) {
                return this.renderInline();
            }

            var renderedContent = $(this.template(this.model.toJSON()));

            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            $('tbody', this.el).append(renderedContent);
            return this;
        }
    });

    /*
     * ## AdUnitView
     *
     * See templates/partials/adunit.html to see how this is rendered in HTML
     * Renders an adunit as a row in a table. Also ads the event handler to
     * submit the price floor change over ajax when the price_floor field is changed.
     */
    var AdUnitView = Backbone.View.extend({
        initialize: function () {
            try {
                this.template = _.template($('#adunit-template').html());
            } catch (e) {
                // you load the template partial in the page. ok if
                // you intend to renderInline.
            }
        },

        /*
         * Render the AdUnit into a table row that already exists. Adds handlers
         * for changing AdUnit attributes over ajax.
         */
        renderInline: function () {
            /*jslint maxlen: 200 */
            var current_model = this.model;
            var adunit_row = $('tr.adunit-row#adunit-' + this.model.id, this.el);
            var metrics = ['rev', 'cpm', 'imp', 'clk', 'ctr', 'fill_rate', 'req', 'att', 'conv', 'conv_rate'];

            _.each(metrics, function (metric) {
                $(metric, adunit_row).text(current_model.get_formatted_stat(metric));
            });

            $('.price_floor', adunit_row).html('<img class="loading-img hidden" ' +
                                               'src="/images/icons-custom/spinner-12.gif">' +
                                               '</img> ' +
                                               '<input id="' + this.model.id + '" ' +
                                               'type="text" ' +
                                               'class="input-text input-text-number number" ' +
                                               'style="width:50px;margin: -3px 0;" ' +
                                               'value="' + this.model.get('price_floor') +
                                               '"> ');
            $('.targeting', adunit_row).html('<img class="loading-img hidden" ' +
                                             'src="/images/icons-custom/spinner-12.gif"></img> ' +
                                             '<input class="targeting-box" type="checkbox">');

            /*jslint maxlen: 110 */

            if (this.model.get('active')) {
                $('input.targeting-box', adunit_row).attr('checked', 'checked');
            }

            // Add the event handler to submit targeting changes over ajax.
            $('input.targeting-box', adunit_row).click(function () {
                var loading_img = $('.targeting .loading-img', adunit_row);
                loading_img.show();
                current_model.save({'active': $(this).is(':checked')}, {
                    success: function () {
                        setTimeout(function () {
                            loading_img.hide();
                        }, 2000);
                    }
                });
            });

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor .input-text', adunit_row).keyup(function () {
                var input_field = $(this);
                input_field.removeClass('error');
                var loading_img = $(".price_floor .loading-img", adunit_row);
                loading_img.show();

                var promise = current_model.save({
                    price_floor: $(this).val()
                });
                if (promise) {
                    promise.success(function () {
                        loading_img.hide();
                    });
                    promise.error(function () {
                        loading_img.hide();
                    });
                } else {
                    loading_img.hide();
                    input_field.addClass('error');
                }
            });


            return this;
        },

        /*
         * Render the adunit model in the template. This assumes that the table
         * row for the app has already been rendered. This will render underneath
         * it's app's row.
         */
        render: function () {
            if(!this.template) {
                return this.renderInline();
            }

            // render the adunit and attach it to the table after it's adunit's row
            var current_model = this.model;
            var renderedContent = $(this.template(this.model.toJSON()));

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor_change', renderedContent)
                .change(function () {
                    current_model.set({'price_floor': $(this).val()});
                    // Save when they click the save button in the price floor cell
                    var save_link = $('.save', $(this).parent());
                    save_link.click(function (e) {
                        e.preventDefault();
                        save_link.addClass('disabled').text('Saving...');
                        current_model.save({}, {
                            success: function () {
                                setTimeout(function () {
                                    save_link.removeClass('disabled').text('Saved');
                                    save_link.text('Save');
                                }, 2000);
                            }
                        });
                    });
                });

            // Add the event handler to submit targeting changes over ajax.
            $('input.targeting-box', renderedContent).click(function () {
                var targeting = $(this).attr('name');
                var activation = $(this).is(':checked') ? 'On' : 'Off';
                $('label[for="' + targeting + '"]', renderedContent).text(activation);

                current_model.set({'active': $(this).is(':checked')});
                current_model.save();
            });

            // Add the right background color based on where the app is in the table
            var app_row = $('tr#app-' + this.model.get('app_id'), this.el);
            var zebra = app_row.hasClass('even') ? 'even' : 'odd';
            renderedContent.addClass(zebra);

            app_row.after(renderedContent);

            return this;
        }
    });

    /*
     * ## AdUnitCollectionView
     */
    var AdUnitCollectionView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('reset', this.render, this);
        },

        render: function () {
            /*jslint maxlen: 200 */

            this.collection.each(function(model) {
                var adunit_row = $('tr.adunit-row#adunit-' + model.id);
                var metrics = ['rev', 'cpm', 'imp', 'clk', 'ctr', 'fill_rate', 'req', 'att', 'conv', 'conv_rate'];

                _.each(metrics, function (metric) {
                    $('.' + metric, adunit_row).text(model.get_formatted_stat(metric));
                });

                /*jslint maxlen: 110 */

                if (model.get('active')) {
                    $('input.targeting-box', adunit_row).attr('checked', 'checked');
                }

                // Add the event handler to submit targeting changes over ajax.
                $('input.targeting-box', adunit_row).click(function () {
                    var loading_img = $('.targeting .loading-img', adunit_row);
                    loading_img.show();
                    model.save({'active': $(this).is(':checked')}, {
                        success: function () {
                            setTimeout(function () {
                                loading_img.hide();
                            }, 2000);
                        }
                    });
                });
            });

            return this;
        },
    });

    window.NetworkDailyCountsView = NetworkDailyCountsView;
    window.AdUnitView = AdUnitView;
    window.AdUnitCollectionView = AdUnitCollectionView;
    window.AppView = AppView;
    window.AdGroupsView = AdGroupsView;
    window.CampaignView = CampaignView;
    window.CollectionGraphView = CollectionGraphView;
    window.NetworkGraphView = NetworkGraphView;

}(this.jQuery, this.Backbone, this._));

