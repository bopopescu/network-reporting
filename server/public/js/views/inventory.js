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

    var ATTRIBUTE_LABELS = {
        rev: "Revenue",
        req: "Requests",
        imp: "Impressions",
        clk: "Clicks",
        att: "Attempts",
        cpm: "CPM",
        fill_rate: "Fill Rate",
        ctr: "CTR"
    };
    
    function getDateLabels(start_date, ticks, interval_type) {
        
        if (ticks === undefined) {
            ticks = 14;
        }

        if (interval_type === undefined) {
            interval_type = 'days';
        }

        if (interval_type !== 'days' && interval_type !== 'hours') {
            throw Error('getDateLabels only accepts "days" or "hours" as an interval_type');
        }

        var current_date = moment(new Date(start_date));

        var labels = [];

        _.times(ticks, function (tick) {
            var label = current_date.format("MM/DD");
            labels.push(label);
            current_date.add(interval_type, 1);
        });

        return labels;
    }


    function createDailyStatsChart(kind, datapoints, labels) {

        $("#stats-chart").html("");

        if (datapoints[kind].length === 1) {
            datapoints[kind].push(datapoints[kind][0]);
        }

        var graph = new Rickshaw.Graph({
	        element: document.querySelector("#stats-chart"),
	        width: 660,
	        height: 160,
	        renderer: 'area',
	        stroke: true,
	        series: [ {
		        data: _.map(datapoints[kind], function (item, iter){
                    return {
                        x: iter,
                        y: item
                    };
                }),
                stroke: 'hsla(200,77%,55%,1)',
                color: 'hsla(205,79%,61%,0.1)'
                
            }]
        });

        graph.renderer.unstack = true;
        graph.render();
        
        // On the X-axis, display the date in MM/DD form.
        var xAxis = new Rickshaw.Graph.Axis.X({
            graph: graph,
            labels: labels,
            ticksTreatment: 'glow'
        });
        
        xAxis.render();
        
        var yAxis = new Rickshaw.Graph.Axis.Y({
            graph: graph,
            tickFormat: Rickshaw.Fixtures.Number.formatKMBT
        });
        yAxis.render();
        
        var hoverDetail = new Rickshaw.Graph.MoPubHoverDetail({
            graph: graph,
            xFormatter: function(x) {
                return moment(labels[x]).format("dddd MMMM Do") + 
                    "<br />" + 
                    "Total: " + 
                    ModelHelpers.format_stat(kind, datapoints[kind][x]) + ' ' + 
                    ATTRIBUTE_LABELS[kind];

            }
        });
    }


    /*
     * # CollectionGraphView
     * Renders a collection as a graph
     */
    var CollectionChartView = Backbone.View.extend({
        el: "#stats",
        initialize: function () {
            try {
                this.template = _.template($('#chart-template').html());
            } catch (e) {}
        },

        render: function() {

            // Setup the stats breakdown on the right side of the chart.
            // The template displays all non-null values, so we update
            // a map of null values to let the template know what we want.
            var this_view = this;
            var template_values = {
                rev: null,
                req: null,
                imp: null,
                clk: null,
                att: null,
                cpm: null,
                fill_rate: null,
                ctr: null
            };

            // Set the active display value so we know which graph and breakdown
            // value to display first.
            var active_display_value = this_view.options.active_display_value || 
                this_view.options.display_values[0];
            template_values['active'] = active_display_value;

            // Create a series list that will keep daily sums for each property.
            // ie rev: [ day 1 total rev, day 2 total rev, etc]
            var series_list = {};
            _.each(this_view.options.display_values, function(display_val) {
                // Override the null template value with formatted
                // value from the collection.
                var formatted_sum = this_view.collection.get_formatted_stat_sum(display_val);
                template_values[display_val] = formatted_sum;

                // Set up the series that will go into the chart.
                var current_series = this_view.collection.get_formatted_stat_series(display_val);
                series_list[display_val] = current_series;
                console.log(current_series);
            });

            // Render the template and the chart with the values we composed
            $(this_view.el).html(this_view.template(template_values));

            var series_date_labels = getDateLabels(this_view.options.start_date, 
                                                   series_list.length);

            createDailyStatsChart(active_display_value,
                                  series_list,
                                  series_date_labels);


            
            $("#stats-breakdown-container tr", this_view.el).click(function() {

                // Remove the active class from the previously active row
                $("#stats-breakdown-container tr.active", this_view.el).removeClass('active');

                // Add the active class to the new table row
                var $this = $(this);
                $this.addClass("active");

                // Create the new chart from the row that was clicked on
                var stats_type = $this.attr('id').replace('stats-breakdown-', '');
                createDailyStatsChart(stats_type,
                                     series_list,
                                     series_date_labels);
            });

        }        
    });


    var CollectionGraphView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },

        show_chart: function () {
            var this_view = this;
            if(this.collection.isFullyLoaded()) {
                var active_chart = $('#dashboard-stats .stats-breakdown .active');
                mopub.Chart.setupDashboardStatsChart('area');
                $('#dashboard-stats-chart').show();
            }
        },

        render: function () {
            var this_view = this;
            if (this_view.collection.isFullyLoaded()) {

                var metrics = [
                    'imp', 
                    'rev', 
                    'clk', 
                    'ctr'
                ];

                // Render the stats breakdown for "all""
                $.each(metrics, function (iter, metric) {
                    var selector = '#stats-breakdown-' + metric + ' .all .inner';
                    $(selector).html(this_view.collection.get_formatted_stat(metric));
                });

                if (this_view.options.yesterday !== null && 
                    this_view.options.today !== null) {

                    // Render the stats breakdown for yesterday
                    $.each(metrics, function (iter, metric) {
                        var selector = '#stats-breakdown-'
                            + metric
                            + ' .yesterday .inner';
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
                        imp: [{'From MoPub': mopub_campaigns.get_total_daily_stats('imp')}, 
                              {'From Networks': network_campaigns.get_total_daily_stats('imp')}],
                        rev: [{'From Networks': {'data': network_campaigns.get_total_daily_stats('rev'), 
                                                 'color': '#e57300'}}],
                        clk: [{'From MoPub': mopub_campaigns.get_total_daily_stats('clk')}, 
                              {'From Networks': network_campaigns.get_total_daily_stats('clk')}],
                        ctr: [{'From MoPub': mopub_campaigns.get_total_daily_stats('ctr')}, 
                              {'From Networks': network_campaigns.get_total_daily_stats('ctr')}],
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
     * See common/templates/partials/app.html to see how this is rendered in HTML.
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

        render: function () {
            if(!this.template) {
                return this.renderInline();
            }

            var renderedContent = $(this.template(this.model.toJSON()));

            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            $('tbody', this.el).append(renderedContent);
            return this;
        },

        renderInline: function () {
            var this_view = this;

            var app_row = $('#app-' + this_view.model.id, this_view.el);
            var metrics = [
                'cpm', 
                'imp', 
                'clk', 
                'ctr', 
                'fill_rate', 
                'req', 
                'att', 
                'conv', 
                'conv_rate',
                'rev'
            ];
            
            _.each(metrics, function (metric) {
                var metric_text = this_view.model.get_formatted_stat(metric);
                $('.' + metric, app_row).text(metric_text);
            });
            /*jslint maxlen: 110 */

            $(".loading-img", app_row).hide();

            return this;
        }
    });

    var NetworkAppView = AppView.extend({
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
                var selector = '';
            }
            var app_row = $('#app-' + this_view.model.id, this_view.el);

            /*jslint maxlen: 200 */
            if (!this_view.options.endpoint_specific 
                || this_view.model.get('stats_endpoint') == 'networks') {
                $('.rev', app_row).text(this_view.model.get_formatted_stat('rev'));
            }
            var metrics = [
                'cpm', 
                'imp', 
                'clk', 
                'ctr', 
                'fill_rate', 
                'req', 
                'att', 
                'conv', 
                'conv_rate'
            ];

            _.each(metrics, function (metric) {
                if (this_view.model.get('stats_endpoint') != 'networks'
                    || this_view.options.network != 'mobfox' 
                    || (metric != 'att' && metric != 'fill_rate')) {
                    $('.' + metric + selector, app_row).text(this_view.model.get_formatted_stat(metric));
                }
            });
            /*jslint maxlen: 110 */

            $(".loading-img", app_row).hide();

            return this;
        }
    });


    /*
     * ## AdUnitView
     *
     * See common/templates/partials/adunit.html to see how this is rendered in HTML
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
            var adunit_row = $('#adunit-' + this.model.id, this.el);
            var metrics = [
                'rev', 
                'cpm', 
                'imp', 
                'clk', 
                'ctr', 
                'fill_rate', 
                'req', 
                'att', 
                'conv', 
                'conv_rate'
            ];

            _.each(metrics, function (metric) {
                var metric_text = current_model.get_formatted_stat(metric);
                $('.' + metric, adunit_row).text(metric_text);
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
        }
    });

    var OrderView = Backbone.View.extend({
        initialize: function () {
            try {
                this.template = _.template($('#campaign-template').html());
            } catch (e) {
                // you load the template partial in the page. ok if
                // you intend to renderInline.
            }
        },

        renderInline: function () {
            var current_model = this.model;
            var order_row = $('#' + current_model.get('key'), this.el);

            var display_fields = [
                'rev',
                'imp',
                'fill_rate',
                'clk',
                'ctr'
            ];
            _.each(display_fields, function(field){
                var field_text = current_model.get_formatted_stat(field);
                $("." + field, order_row).text(field_text);
            });
            $(".lineitems", order_row).text(current_model.get('adgroups').length);
            $(".loading-img", order_row).hide();
        }

    });


    var LineItemView = Backbone.View.extend({
        initialize: function () {
            try {
                this.template = _.template($('#adgroup-template').html());
            } catch (e) {
                // you load the template partial in the page. ok if
                // you intend to renderInline.
            }
        },

        renderInline: function () {
            var current_model = this.model;
            var row = $('#' + current_model.get('key'), this.el);
            var display_fields = [
                'rev',
                'imp',
                'fill_rate',
                'clk',
                'ctr',
                'conv'
            ];
            _.each(display_fields, function(field){
                $("." + field, row).text(current_model.get_formatted_stat(field));
            });

            var popover_template = ""
                + "<p>Ran from <%= start_datetime %> to <%= end_datetime %>." 
                + "<br /> <br />"
                + "It <strong>did/did not</strong> meet it's goal of [goal]." 
                + "<br /> <br />"
                + "Targeting 3 Ad Units"
                + "</p>";
            popover_template = _.template(popover_template);

            var popover_content = popover_template(current_model.toJSON());

            $(".moreinfo", row).popover({
                placement: 'bottom',
                title: "About this line item",
                content: popover_content,
                delay: { hide: 250 }            
            });
        }
    });

    window.AdUnitView = AdUnitView;
    window.AppView = AppView;

    window.LineItemView = LineItemView;
    window.OrderView = OrderView;

    window.CollectionGraphView = CollectionGraphView;
    window.CollectionChartView = CollectionChartView;

    window.NetworkGraphView = NetworkGraphView;

}(this.jQuery, this.Backbone, this._));

