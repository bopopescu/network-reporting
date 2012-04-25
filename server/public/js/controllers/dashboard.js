/*
 * # MoPub Dashboard
 */

var mopub = mopub || {};

(function($, Backbone, _){

    /*
     * Settings
     */

    var URL = 'http://ec2-23-22-32-218.compute-1.amazonaws.com/';
    //var URL = 'http://localhost:8888/';

    // Color theme for the charts and table rows.
    var COLOR_THEME = {
        primary: [
            'rgba(200,225,251,0.4)',
            'rgba(163,193,218,0.4)',
            'rgba(236,183,150,0.4)',
            'rgba(178,164,112,0.4)',
            'rgba(210,237,130,0.4)',
            'rgba(221,203,83,0.4)'
        ],
        secondary: [
            'rgba(200,225,251,1)',
            'rgba(158,177,193,1)',
            'rgba(220,143,112,1)',
            'rgba(146,135,90,1)',
            'rgba(187,228,104,1)',
            'rgba(197,163,47,1)'
        ]
    };

    // Map of property name to it's title
    var STATS = {
        'attempts': 'Attempts',
        'clk': 'Clicks',
        'conv': 'Conversions',
        'conv_rate': 'Conversion Rate',
        'cpm': 'CPM',
        'ctr': 'CTR',
        'fill_rate': 'Fill Rate',
        'imp': 'Impressions',
        'req': 'Requests',
        'rev': 'Revenue'
    };

    var ADVERTISER_COLUMNS = [
        'rev',
        'imp',
        'clk',
        'ctr',
        'cpm',
        'attempts',
        'conv',
        'conv_rate'
    ];

    var ADVERTISER_DEFAULT_COLUMNS = [
        'rev',
        'imp',
        'clk'
    ];

    var PUBLISHER_COLUMNS = [
        'rev',
        'imp',
        'clk',
        'ctr',
        'cpm',
        'attempts',
        'conv',
        'conv_rate',
        'fill_rate',
        'req'
    ];

    var PUBLISHER_DEFAULT_COLUMNS = [
        'rev',
        'imp',
        'clk'
    ];

    var SORTABLE_COLUMNS = [
        'attempts',
        'clk',
        'conv',
        'imp',
        'req',
        'rev'
    ];

    var MAX_CAMPAIGNS = 6;
    var MAX_APPS = 12;
    var MAX_ADUNITS = 6;

    var WIDTH = 500;
    var HEIGHT = 125;

    var MARGIN_TOP = 10;
    var MARGIN_RIGHT = 30;
    var MARGIN_BOTTOM = 15;
    var MARGIN_LEFT = 50;

    /*
     * Helper functions
     */

    /*
     * Pops up a growl-style message when something has
     * gone wrong fetching data. Use this to catch 500/503
     * errors from the server.
     */
    var toast_error = function () {
        var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

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

    /*
     * Gets a date string (MM/DD) from a datapoint object with a
     * stringified date or hour field (like the one we'd get
     * in a response from the stats service).
     */
    function get_date_from_datapoint(datapoint) {
        var timeslice = null;
        if (datapoint.hasOwnProperty('hour')) {
            timeslice = moment(datapoint['hour'], "YYYY-MM-DD-HH");
            timeslice = timeslice.format('M/D HH:00');
        } else if (datapoint.hasOwnProperty('date')) {
            timeslice = moment(datapoint['date'], "YYYY-MM-DD-HH");
            timeslice = timeslice.format('M/D');
        }
        return timeslice;
    }


    /*
     * Formats a number for display based on a property name.
     * Currency will get a $, percentages will get a %. All numbers
     * will be formatted with commas and KMBT.
     */
    function format_stat(stat, value) {
        switch (stat) {
          case 'attempts':
          case 'clk':
          case 'conv':
          case 'imp':
          case 'req':
            return format_kmbt(value, true);
          case 'cpm':
          case 'rev':
            return '$' + format_kmbt(value, true);
          case 'conv_rate':
          case 'ctr':
          case 'fill_rate':
            return mopub.Utils.formatNumberAsPercentage(value);
        default:
            throw new Error('Unsupported stat "' + stat + '".');
        }
    }

    /*
     * Formats a number in KMBT (thousands, millions,
     * billions, trillions) formatting.
     *
     * Example: 1000000 -> 1M, 1230000000 -> 12.3B
     */
    function format_kmbt(number, with_decimal) {

        if (with_decimal === undefined) {
            with_decimal = false;
        }

        // Numbers greater than this are ridiculous and
        // so we aren't supporting their existance.
        if (number > 999999999999999.999) {
            return number;
        }

        //var endings = ['', 'K', 'M', 'B', 'T', 'Qd', 'Qn', 'Sx'];
        var endings = ['', 'K', 'M', 'B', 'T'];

        var with_commas = mopub.Utils.formatNumberWithCommas(number);
        var parts = with_commas.split(',');

        if (parts.length > 1 && with_decimal) {
            var decimal = "." + parts[1].substring(0,2);
            return "" + parts[0] + decimal + endings[parts.length-1];
        } else if (parts.length > 1) {
            return "" + parts[0] + endings[parts.length-1];
        } else {
            var n = "" + number;
            if (n.indexOf('.') >= 0) {
                return n.substring(0, n.indexOf('.') + 3);
            } else if (with_decimal) {
                return n + ".00";
            } else {
                return n;
            }
        }
    }


    // Calculates conversion rate, cpm, ctr, and fill_rate for an object.
    // The object is in the form that we normally expect from the server.
    // The new keys and values are set on the object in place, so nothing
    // is returned.
    function calculate_stats(obj) {
        obj.conv_rate = obj.imp === 0 ? 0 : obj.conv / obj.imp;
        obj.cpm = obj.imp === 0 ? 0 : 1000 * obj.clk / obj.imp;
        obj.ctr = obj.imp === 0 ? 0 : obj.clk / obj.imp;
        obj.fill_rate = obj.req === 0 ? 0 : obj.imp / obj.req;
    }

    function pad(integer) {
        return integer < 10 ? '0' + integer : integer;
    }

    function string_to_date(date_string) {
        var parts = date_string.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }

    function date_to_string(date) {
        return date.getFullYear() + '-' +
            (date.getMonth() + 1) + '-' +
            date.getDate();
    }

    function pretty_string_to_date(date_string) {
        var parts = date_string.split('/');
        return new Date(parts[2], parts[0] - 1, parts[1]);
    }

    function date_to_pretty_string(date) {
        return pad(date.getMonth() + 1) + '/' + pad(date.getDate()) + '/' + date.getFullYear();
    }

    function string_to_date_hour(date_string) {
        var parts = date_string.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2], parts[3]);
    }

    function date_hour_to_string(date) {
        return date.getFullYear() +
            '-' + (date.getMonth() + 1) +
            '-' + date.getDate() +
            '-' + date.getHours();
    }

    function get_charts() {
        return ['rev', 'imp', 'clk', 'ctr'];
    }


    /*
     * Create a new chart using Rickshaw/d3.
     *
     * `series` is the type of series we're representing (e.g. 'rev',
     * 'imp', 'clk') and is used for formatting axes and tooltips.
     *
     * `element` is the name of the element (e.g. '#chart') to render
     * the chart in. The chart will be rendered when the function is
     * called.
     *
     * `account_data` is all of the data you get back from a query.
     *
     * `options` is not currently used, but will be used in the future
     * to specify stuff like height, width, and other rendering options.
     */
    function createChart(series, element, account_data, options) {
        var all_chart_data = _.map(account_data, function(range, i){
            var stroke;
            var color;
            if(range.id === 'vs') {
                stroke = 'rgba(223, 223, 223, 1.0)';
                color = 'rgba(223, 223, 223, 0.4)';
            }
            else {
                stroke = COLOR_THEME.secondary[i];
                color = COLOR_THEME.primary[i];
            }
            var individual_series_data = {
                data: _.map(range, function(datapoint, j){
                    return {
                        x: j,
                        y: datapoint[series]
                    };
                }),
                stroke: stroke,
                color: color
            };
            return individual_series_data;
        });

        // Hack to clear any current charts from the element. Rickshaw
        // doesn't remove the old chart from the element before it
        // renders a new one, so we have to do it manually.
        $(element).html('');

        var graph_tension = all_chart_data[0].length > 7 ? 0.8 : 1.0;

        // Create the new chart with our series data
        var chart = new Rickshaw.Graph({
            element: document.querySelector(element),
            width: WIDTH,
            height: HEIGHT,
            renderer: 'area',
            stroke: true,
            tension: 1.0,
            series: all_chart_data

        });

        // When the graph is hovered over, we display the date and the
        // current value in a tooltip at the top.
        var hoverDetail = new Rickshaw.Graph.MoPubHoverDetail( {
            graph: chart,
            xFormatter: function(x) {
                var labels = _.map(account_data, function(range){
                    var single_datapoint = range[x];
                    var date = get_date_from_datapoint(single_datapoint);
                    var formatted_stat = format_stat(series, single_datapoint[series]);

                    return date + ": " + formatted_stat;
                });

                return labels.join('<br />');
            }
            // yFormatter: function(y) {
            //     return format_stat(series, y);
            // }
        });

        // On the X-axis, display the date in MM/DD form.
        var xAxis = new Rickshaw.Graph.Axis.X({
	        graph: chart,
            labels: _.map(account_data[0], function(datapoint){
                return get_date_from_datapoint(datapoint);
            }),
	        ticksTreatment: 'glow'
        });

        xAxis.render();

        // On the Y-axis, display the amount in KMBT form.
        var yAxis = new Rickshaw.Graph.Axis.Y({
	        graph: chart,
	        ticksTreatment: 'glow',
            tickFormat: Rickshaw.Fixtures.Number.formatKMBT
        } );

        yAxis.render();

        // Render and return the chart
        chart.renderer.unstack = true;
        chart.render();
        return chart;
    }


    /*
     * Initialization function that renders all 4 of the charts in the
     * dashboard page.
     */
    function initializeDashboardCharts(account_data) {
        var rev_chart = createChart('rev', '#rev_chart', account_data);
        var imp_chart = createChart('imp', '#imp_chart', account_data);
        var clk_chart = createChart('clk', '#clk_chart', account_data);
        var ctr_chart = createChart('ctr', '#ctr_chart', account_data);
    }


    var DashboardHelpers = {
        get_date_from_datapoint: get_date_from_datapoint,
        format_stat: format_stat,
        format_kmbt: format_kmbt,
        string_to_date: string_to_date,
        date_to_string: date_to_string,
    };

    var DashboardController = {
        initializeDashboard: function(bootstrapping_data) {
            /**
             * @param {object} bootstrapping_data: {
             *     account: account key,
             *     names: {
                       key: name
             *     }
             * }
             */

            // Set up JSONP. We calculate derivative stats upon every
            // query response.
            $.jsonp.setup({
                callbackParameter: "callback",
                dataFilter: function (json) {
                    _.each(['sum', 'vs_sum'], function (key) {
                        _.each(json[key], function (obj) {
                            calculate_stats(obj);
                        });
                    });
                    _.each(['daily', 'hourly', 'vs_daily', 'vs_hourly', 'top', 'vs_top'], function (key) {
                        _.each(json[key], function (list) {
                            _.each(list, function (obj) {
                                calculate_stats(obj);
                            });
                        });
                    });
                    return json;
                },
                error: toast_error,
                url: URL
            });


            function get_keys(type) {
                if(((type == 'source' || type == 'campaign') &&
                    !$('tr.source.selected, tr.campaign.selected')) ||
                   ((type == 'app' || type == 'adunit') &&
                    !$('tr.app.selected, tr.adunit.selected'))) {

                    return _.map($('tr.' + type), function (tr) {
                        return tr.id;
                    });
                }

                return _.map($('tr.' + type + '.selected'), function (tr) {
                    return tr.id;
                });
            }

            function get_advertiser_type() {
                // if nothing is checked, return null
                if($('tr.selected', 'table#advertiser').length === 0) {
                    return null;
                }

                var use_source = true;
                $('tr.source', 'table#advertiser').each(function (index, source) {
                    if(!$(source).hasClass('selected')) {
                        $(source).nextUntil('tr.source').each(function (index, campaign) {
                            if($(campaign).hasClass('selected')) {
                                use_source = false;
                            }
                        });
                    }
                });
                if(use_source) {
                    return 'source';
                }

                return 'campaign';
            }

            function get_publisher_type() {
                // if nothing is checked, return null
                if($('tr.selected', 'table#publisher').length === 0) {
                    return null;
                }

                var use_app = true;
                $('tr.app', 'table#publisher').each(function (index, app) {
                    if(!$(app).hasClass('selected')) {
                        $(app).nextUntil('tr.app').each(function (index, adunit) {
                            if($(adunit).hasClass('selected')) {
                                use_app = false;
                            }
                        });
                    }
                });
                if(use_app) {
                    return 'app';
                }

                return 'adunit';
            }

            function get_advertiser_query(advertiser) {
                var query = {};
                if(advertiser) {
                    query[advertiser] = get_keys(advertiser);
                }
                return query;
            }

            function get_publisher_query(publisher) {
                var query = {};
                if(publisher) {
                    query[publisher] = get_keys(publisher);
                }
                return query;
            }

            /* Templates */
            var filter_body_row = _.template($('#filter_body_row').html());
            var names = bootstrapping_data.names;

            function render_filter_body_row(data, columns, default_columns, order, hidden, hide) {
                var context = {
                    type: data.type,
                    id: data.id,
                    selected: data.selected,
                    name: names[data.id],
                    columns: columns,
                    default_columns: default_columns,
                    hidden: hidden,
                    hide: hide,
                    sorted: order,
                    stats: {}
                };

                _.each(columns, function (stat) {
                    context.stats[stat] = format_stat(stat, data.stats[stat]);
                });

                if('vs_stats' in data) {
                    context.stats_delta = {};
                    context.stats_delta_class = {};
                    _.each(columns, function (stat) {
                        if(data.vs_stats[stat] === 0) {
                            context.stats_delta[stat] = '';
                            context.stats_delta_class[stat] = '';
                        }
                        else {
                            var delta = Math.round(100 * (data.stats[stat] - data.vs_stats[stat]) / data.vs_stats[stat]);
                            if(delta === 0) {
                                context.stats_delta[stat] = '~0%';
                                context.stats_delta_class[stat] = '';
                            }
                            else if(delta < 0) {
                                context.stats_delta[stat] = delta + '%';
                                context.stats_delta_class[stat] = 'negative';
                            }
                            else {
                                context.stats_delta[stat] = '+' + delta + '%';
                                context.stats_delta_class[stat] = 'positive';
                            }
                        }
                    });
                }

                return filter_body_row(context);
            }

            function get_data() {
                var start = $('#start').val();
                var end = $('#end').val();

                var data = {
                    account: bootstrapping_data['account'],
                    start: start,
                    end: end
                };

                if($('#vs_start').val() && $('#vs_end').val()) {
                    data['vs_start'] = $('#vs_start').val();
                    data['vs_end'] = $('#vs_end').val();
                }

                return data;
            }

            function update_dashboard(update_rollups_and_charts, advertiser_table, publisher_table) {
                var data = get_data();

                var advertiser_type = get_advertiser_type();
                var advertiser_query = get_advertiser_query(advertiser_type);
                var publisher_type = get_publisher_type();
                var publisher_query = get_publisher_query(publisher_type);

                record_metric('Updated dashboard data', {
                    advertiser: '' + advertiser_query,
                    publisher: '' + publisher_query
                });

                if(update_rollups_and_charts) {
                    var rollups_and_charts_data = _.clone(data);
                    var granularity = get_granularity();
                    rollups_and_charts_data.granularity = granularity;
                    rollups_and_charts_data.query = [_.extend(_.clone(advertiser_query), publisher_query)];

                    if(advertiser_comparison_shown()) {
                        $('tr.selected', '#advertiser').each(function (index, tr) {
                            var query = _.clone(publisher_query);
                            if($(tr).hasClass('source')) {
                                query.source = [tr.id];
                            }
                            else {
                                query.campaign = [tr.id];
                            }
                            rollups_and_charts_data.query.push(query);
                        });

                        $.jsonp({
                            data: {
                                data: JSON.stringify(rollups_and_charts_data)
                            },
                            success: function (json, textStatus) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    update_rollups(json.sum[0]);
                                    var charts_data = json[granularity].slice(1);
                                    initializeDashboardCharts(charts_data);
                                });
                            }
                        });
                    } else if(publisher_comparison_shown()) {
                        $('tr.selected', '#publisher').each(function (index, tr) {
                            var query = _.clone(advertiser_query);
                            if($(tr).hasClass('app')) {
                                query.app = [tr.id];
                            }
                            else {
                                query.adunit = [tr.id];
                            }
                            rollups_and_charts_data.query.push(query);
                        });

                        console.log(rollups_and_charts_data);

                        $.jsonp({
                            data: {
                                data: JSON.stringify(rollups_and_charts_data)
                            },
                            success: function (json, textStatus) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    update_rollups(json.sum[0]);
                                    var charts_data = json[granularity].slice(1);
                                    initializeDashboardCharts(charts_data);
                                });
                            }
                        });
                    } else {
                        $.jsonp({
                            data: {
                                data: JSON.stringify(rollups_and_charts_data)
                            },
                            success: function (json, textStatus) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    var charts_data;
                                    if(json.vs_sum.length) {
                                        update_rollups(json.sum[0], json.vs_sum[0]);
                                        charts_data = [
                                            _.clone(json[granularity][0]),
                                            _.extend(_.clone(json['vs_' + granularity][0]), { id: 'vs' })
                                        ];
                                    } else {
                                        update_rollups(json.sum[0]);
                                        charts_data = [json[granularity][0]];
                                    }
                                    initializeDashboardCharts(charts_data);
                                });
                            }
                        });
                    }
                }

                if (advertiser_table) {
                    update_advertiser_table(data, publisher_query, get_advertiser_order());
                }

                if (publisher_table) {
                    update_publisher_table(data, advertiser_query, get_publisher_order(), PUBLISHER_DEFAULT_COLUMNS);
                }
            }

            function update_rollups(data, vs_data) {
                _.each(get_charts(), function (stat) {

                    var rollup = $('#' + stat + ' > div');
                    rollup.children('div.value').html(format_stat(stat, data[stat]));

                    if (vs_data && vs_data[stat] !== 0) {
                        var delta = rollup.children('div.delta');
                        var val = Math.round(100 * (data[stat] - vs_data[stat]) / vs_data[stat]);
                        var html = '';
                        if (val > 0) {
                            html += '+';
                            delta.removeClass('negative');
                            delta.addClass('positive');
                        } else if (val < 0) {
                            delta.removeClass('positive');
                            delta.addClass('negative');
                        } else {
                            html += '~';
                            delta.removeClass('positive');
                            delta.removeClass('negative');
                        }
                        html += val + '%';
                        delta.html(html);
                    } else {
                        rollup.children('div.delta').html('');
                    }
                });
            }

            /* Tables */
            function update_advertiser_table(data, publisher_query, order) {
                var selected = _.map($('tr.selected', '#advertiser'), function (tr) { return tr.id; });

                var source_data = _.clone(data);
                source_data.query = _.map(['direct', 'mpx', 'network'], function (source) {
                    var query = _.clone(publisher_query);
                    query.source = [source];
                    return query;
                });

                $.jsonp({
                    data: {
                        data: JSON.stringify(source_data)
                    },
                    success: function (json) {
                        // defer so exceptions show up in the console
                        _.defer(function() {
                            var sources = [];
                            _.each(source_data.query, function(query, index) {
                                var source = {
                                    type: 'source',
                                    id: query.source[0],
                                    selected: _.include(selected, query.source[0]),
                                    stats: json.sum[index]
                                };
                                if(json.vs_sum.length) {
                                    source.vs_stats = json.vs_sum[index];
                                }
                                sources.push(source);
                            });
                            update_sources(data, publisher_query, order, selected, sources);
                        });
                    }
                });
            }

            function update_sources(data, publisher_query, order, selected, sources) {
                $('tr.campaign', 'table#advertiser').remove();

                _.each(sources, function (source) {
                    var $source = $(render_filter_body_row(source, ADVERTISER_COLUMNS, ADVERTISER_DEFAULT_COLUMNS, order, $('table#advertiser th.hidden').length, false));
                    if(advertiser_comparison_shown()) {
                        $source.css('background-color', COLOR_THEME.primary[selected.indexOf(source.id)]);
                    }
                    if($('#' + source.id).length) {
                        $('#' + source.id).replaceWith($source);
                    }
                    else {
                        $('#advertiser').append($source);
                    }
                    if(source.id == 'direct' || source.id == 'network') {
                        var campaign_data = _.clone(data);
                        campaign_data.granularity = 'top';
                        campaign_data.query = [_.extend(_.clone(publisher_query), {
                            source: [source.id],
                            order: order,
                            top: 'campaign'
                        })];

                        $.jsonp({
                            data: {
                                data: JSON.stringify(campaign_data)
                            },
                            success: function(json) {
                                // defer so exceptions show up in the console
                                _.defer(function() {
                                    var campaigns = [];
                                    _.each(json.top[0], function(top, index) {
                                        var campaign = {
                                            type: 'campaign',
                                            id: top.campaign,
                                            selected: _.include(selected, top.campaign) || (!advertiser_comparison_shown() && _.include(selected, source.id)),
                                            stats: top
                                        };
                                        if(json.vs_top.length) {
                                            campaign.vs_stats = json.vs_top[0][index];
                                        }
                                        campaigns.push(campaign);
                                    });
                                    update_campaigns(order, $source, campaigns, order);
                                });
                            },
                            url: URL + 'topN/'
                        });
                    }
                });
            }

            function update_campaigns(order, $source, campaigns) {
                var $last = $source;
                _.each(campaigns, function (campaign, index) {
                    var $campaign = $(render_filter_body_row(campaign, ADVERTISER_COLUMNS, ADVERTISER_DEFAULT_COLUMNS, order, $('table#advertiser th.hidden').length, index >= MAX_CAMPAIGNS));
                    if(advertiser_comparison_shown()) {
                        $campaign.css('background-color', COLOR_THEME.primary[selected.indexOf(campaign.id)]);
                    }
                    $last.after($campaign);
                    $last = $campaign;
                });

                // hide unselected rows' stats
                if($('tbody tr.selected', 'table#advertiser').length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', 'table#advertiser').show();
                }
                else {
                    $('tbody tr', 'table#advertiser').each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }
            }

            function update_publisher_table(data, advertiser_query, order) {
                selected = _.map($('tr.selected'), function (tr) { return tr.id; });

                $('tr.app, tr.adunit', 'table#publisher').remove();

                var app_data = _.clone(data);
                app_data.granularity = 'top';
                app_data.query = [_.extend(_.clone(advertiser_query), {
                    order: order,
                    top: 'app'
                })];

                $.jsonp({
                    data: {
                        data: JSON.stringify(app_data)
                    },
                    success: function(json) {
                        // defer so exceptions show up in the console
                        _.defer(function() {
                            var apps = [];
                            _.each(json.top[0], function(top, index) {
                                var app = {
                                    type: 'app',
                                    id: top.app,
                                    selected: _.include(selected, top.app),
                                    stats: top
                                };
                                if(json.vs_top.length) {
                                    app.vs_stats = json.vs_top[0][index];
                                }
                                apps.push(app);
                            });
                            update_apps(data, advertiser_query, order, selected, apps);
                        });
                    },
                    url: URL + 'topN/'
                });
            }

            function update_apps(data, advertiser_query, order, selected, apps) {
                _.each(apps, function (app, index) {
                    var $app = $(render_filter_body_row(app, PUBLISHER_COLUMNS, PUBLISHER_DEFAULT_COLUMNS, order, $('table#publisher th.hidden').length, index >= MAX_APPS));
                    if(publisher_comparison_shown()) {
                        $app.css('background-color', COLOR_THEME.primary[selected.indexOf(app.id)]);
                    }
                    $publisher_table.append($app);

                    var adunit_data = _.clone(data);
                    adunit_data.granularity = 'top';
                    adunit_data.query = [_.extend(_.clone(advertiser_query), {
                        app: [app.id],
                        order: order,
                        top: 'adunit'
                    })];

                    $.jsonp({
                        data: {
                            data: JSON.stringify(adunit_data)
                        },
                        success: function (json) {
                            // defer so exceptions show up in the console
                            _.defer(function() {
                                var adunits = [];
                                _.each(json.top[0], function(top, index) {
                                    var adunit = {
                                        type: 'adunit',
                                        id: top.adunit,
                                        selected: _.include(selected, top.adunit) || (!publisher_comparison_shown() && _.include(selected, app.id)),
                                        stats: top
                                    };
                                    if(json.vs_top.length) {
                                        adunit.vs_stats = json.vs_top[0][index];
                                    }
                                    adunits.push(adunit);
                                });
                                update_adunits(order, $app, adunits, $('table#publisher th.hidden').length, index >= MAX_APPS);
                            });
                        },
                        url: URL + 'topN/'
                    });
                });
            }

            function update_adunits(order, $app, adunits, hide) {
                var $last = $app;
                _.each(adunits, function (adunit, index) {
                    var $adunit = $(render_filter_body_row(adunit, PUBLISHER_COLUMNS, PUBLISHER_DEFAULT_COLUMNS, order, hide || $('table#publisher th.hidden').length, index >= MAX_ADUNITS));
                    if(publisher_comparison_shown()) {
                        $adunit.css('background-color', COLOR_THEME.primary[selected.indexOf(adunit.id)]);
                    }
                    $last.after($adunit);
                    $last = $adunit;
                });

                // hide unselected rows' stats
                if($('tbody tr.selected', 'table#publisher').length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', 'table#publisher').show();
                }
                else {
                    $('tbody tr', 'table#publisher').each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }
            }


            /* Date Range */

            // TODO: move?
            /**
             * @return {Date} today's date with time zero
             */
            function get_today() {
                var now = new Date();
                return new Date(now.getFullYear(), now.getMonth(), now.getDate());
            }

            /**
             * @param {string} start_end 'today', 'yesterday', 'last_7_days',
             *     'last_14_days', or 'custom'
             */
            function update_start_end(start_end) {
                var start, end;
                if(start_end == 'custom') {
                    start = pretty_string_to_date($('#custom_start').val());
                    end = pretty_string_to_date($('#custom_end').val());
                    end.setHours(23);
                }
                else {
                    switch(start_end) {
                        case 'today':
                            start = get_today();
                            end = get_today();
                            break;
                        case 'yesterday':
                            start = new Date(get_today() - 86400000);
                            end = new Date(get_today() - 86400000);
                            break;
                        case 'last_7_days':
                            start = new Date(get_today() - 86400000 * 6);
                            end = get_today();
                            break;
                        case 'last_14_days':
                            start = new Date(get_today() - 86400000 * 13);
                            end = get_today();
                            break;
                    }
                    end.setHours(23);

                    $('#custom_start').val(date_to_pretty_string(start));
                    $('#custom_end').val(date_to_pretty_string(end));
                }

                $('#start').val(date_hour_to_string(start));
                $('#end').val(date_hour_to_string(end));

                if(start_end == 'today' || start_end == 'yesterday') {
                    $('#start_end_label').html(date_to_pretty_string(start));
                }
                else {
                    $('#start_end_label').html(date_to_pretty_string(start) + ' to ' + date_to_pretty_string(end));
                }

                $('#vs li').hide();
                $('#vs li.' + start_end).show();

                update_vs_start_end('none');
                return {
                    'start': start,
                    'end': end
                };
            }

            $('#today, #yesterday, #last_7_days, #last_14_days').click(function () {
                update_start_end(this.id);
                record_metric('Changed date', {'date_range': this.id});
                update_dashboard(true, true, true);
            });

            $('#custom').click(function() {
                $('#date_modal').show();
            });

            $('#date_modal_submit').click(function () {
                $('#date_modal').hide();
                var dates = update_start_end('custom');
                record_metric('Changed date', {
                    date_range: 'custom',
                    start: dates.start,
                    end: dates.end
                });
                update_dashboard(true, true, true);
            });

            $('#date_modal_cancel').click(function () {
                $('#date_modal').hide();
            });


            /* Comparison Date Range */
            function update_vs_start_end(vs_start_end) {
                if(vs_start_end == 'none') {
                    $('#vs_start').val('');
                    $('#vs_end').val('');
                    $('#vs_start_end_label').html('None');
                }
                else {
                    hide_advertiser_comparison();
                    hide_publisher_comparison();

                    var start = string_to_date_hour($('#start').val());
                    var end = string_to_date_hour($('#end').val());
                    var diff;
                    switch(vs_start_end) {
                        case 'day':
                            diff = 86400000;
                            break;
                        case 'week':
                            diff = 86400000 * 7;
                            break;
                        case '14_days':
                            diff = 86400000 * 14;
                            break;
                    }
                    var vs_start = new Date(start - diff);
                    var vs_end = new Date(end - diff);

                    $('#vs_start').val(date_hour_to_string(vs_start));
                    $('#vs_end').val(date_hour_to_string(vs_end));

                    if(vs_start_end == 'day' || (vs_start_end == 'week' && end - start <= 86400000)) {
                        $('#vs_start_end_label').html(date_to_pretty_string(vs_start));
                    }
                    else {
                        $('#vs_start_end_label').html(date_to_pretty_string(vs_start) + ' to ' + date_to_pretty_string(vs_end));
                    }
                }
            }

            $('#none, #day, #week, #14_days').click(function () {
                update_vs_start_end(this.id);
                record_metric('Changed vs date', {
                    date_range: $(this).attr('id')
                });
                update_dashboard(true, true, true);
            });


            /* Granularity */
            function get_granularity() {
                return 'daily';
            }


            /* Export */
            $('button#export').click(function () {
                $('#export_wizard').modal('show');
            });
            $('button#download').click(function () {
                // Hide the modal when the download button is clicked.
                $('#export_wizard').modal('hide');

                var data = get_data();

                // Determine the query
                var query = {};

                var advertiser_breakdown = $('select[name="advertiser_breakdown"]').val();
                query[advertiser_breakdown] = get_keys(advertiser_breakdown);
                var publisher_breakdown = $('select[name="publisher_breakdown"]').val();
                query[publisher_breakdown] = get_keys(publisher_breakdown);

                // REFACTOR: this can be removed once we have real data in the tables
                // Map id's to names so that we can include them in the table
                var names = {};
                _.each(query[advertiser_breakdown], function(id) {
                    names[id] = $.trim($('#' + id + ' td.name').html());
                });
                _.each(query[publisher_breakdown], function(id) {
                    names[id] = $.trim($('#' + id + ' td.name').html());
                });

                _.extend(data, {
                    granularity: get_granularity(),
                    advertiser_breakdown: advertiser_breakdown,
                    publisher_breakdown: publisher_breakdown,
                    query: query,
                    names: names
                });

                record_metric('Dashboard Export', {
                    advertiser_breakdown: data.advertiser_breakdown,
                    publisher_breakdown: data.publisher_breakdown
                });

                window.location = URL + 'csv/?data=' + JSON.stringify(data);
            });


            /**
             * TABLES
             */

            var $advertiser_table = $('#advertiser');
            var $publisher_table = $('#publisher');


            /* Advertiser/Publisher Comparison */
            var $advertiser_comparison = $('#advertiser_comparison');

            function advertiser_comparison_shown() {
                return $advertiser_comparison.hasClass('hide');
            }

            function show_advertiser_comparison() {
                $advertiser_comparison.addClass('hide');
                $advertiser_comparison.removeClass('show');

                // default comparison selection: all sources
                $('tr.source', $advertiser_table).addClass('selected');
                $('tr.campaign', $advertiser_table).removeClass('selected');

                update_advertiser_colors();
            }

            function hide_advertiser_comparison() {
                $advertiser_comparison.addClass('show');
                $advertiser_comparison.removeClass('hide');

                // select subcomponents of selected
                $('tr.source.selected', $advertiser_table).each(function (index, tr) {
                    $(tr).nextUntil('tr.source').addClass('selected');
                });

                update_advertiser_colors();
            }

            $advertiser_comparison.click(function () {
                if(advertiser_comparison_shown()) {
                    hide_advertiser_comparison();
                }
                else {
                    update_vs_start_end('none');
                    hide_publisher_comparison();
                    show_advertiser_comparison();
                }

                update_dashboard(true, false, false);
            });

            var $publisher_comparison = $('#publisher_comparison');

            function publisher_comparison_shown() {
                return $publisher_comparison.hasClass('hide');
            }

            function show_publisher_comparison() {
                $publisher_comparison.addClass('hide');
                $publisher_comparison.removeClass('show');

                // default comparison selection: all apps
                $('tr.app', $publisher_table).addClass('selected');
                $('tr.adunit', $publisher_table).removeClass('selected');

                update_publisher_colors();
            }

            function hide_publisher_comparison() {
                $publisher_comparison.addClass('show');
                $publisher_comparison.removeClass('hide');

                // select subcomponents of selected
                $('tr.app.selected', $publisher_table).each(function (index, tr) {
                    $(tr).nextUntil('tr.app').addClass('selected');
                });

                update_publisher_colors();
            }

            $publisher_comparison.click(function () {
                if(publisher_comparison_shown()) {
                    hide_publisher_comparison();
                }
                else {
                    update_vs_start_end('none');
                    hide_advertiser_comparison();
                    show_publisher_comparison();
                }

                update_dashboard(true, false, false);
            });

            /* Columns */
            var $advertiser_columns = $('#advertiser_columns');

            function advertiser_columns_shown() {
                return $advertiser_columns.hasClass('hide');
            }

            $advertiser_columns.click(function () {
                if(advertiser_columns_shown()) {
                    $advertiser_columns.addClass('hide');
                    $advertiser_columns.removeClass('show');

                    $('th, td', $advertiser_table).show();

                    record_metric('Showed advertiser columns');
                }
                else {
                    $advertiser_columns.addClass('show');
                    $advertiser_columns.removeClass('hide');

                    _.each(ADVERTISER_COLUMNS, function (column) {
                        if(!_.include(ADVERTISER_DEFAULT_COLUMNS, column) && column !== get_advertiser_order()) {
                            $('th.' + column + ', td.' + column, $advertiser_table).hide();
                        }
                    });

                    record_metric('Hid advertiser columns');
                }
            });

            var $publisher_columns = $('#publisher_columns');

            function publisher_columns_shown() {
                return $publisher_columns.hasClass('hide');
            }

            $publisher_columns.click(function () {
                if(publisher_columns_shown()) {
                    $publisher_columns.addClass('hide');
                    $publisher_columns.removeClass('show');

                    $('th, td', $publisher_table).show();

                    record_metric('Showed publisher columns');
                }
                else {
                    $publisher_columns.addClass('show');
                    $publisher_columns.removeClass('hide');

                    _.each(PUBLISHER_COLUMNS, function (column) {
                        if(!_.include(PUBLISHER_DEFAULT_COLUMNS, column) && column !== get_publisher_order()) {
                            $('th.' + column + ', td.' + column, $publisher_table).hide();
                        }
                    });

                    record_metric('Hid publisher columns');
                }
            });


            /* Order */
            var $advertiser_order = $('#advertiser_order');

            function get_advertiser_order() {
                return $advertiser_order.val();
            }

            $('th.sortable', $advertiser_table).live('click', function () {
                var $th = $(this);
                var order;
                _.each(STATS, function (title, stat) {
                    if($th.hasClass(stat)) {
                        order = stat;
                        $advertiser_order.val(stat);
                    }
                });

                $('th.sortable', $advertiser_table).removeClass('sorted');
                $('th.' + order, $advertiser_table).addClass('sorted');

                record_metric('Sorted advertiser table', {dimension: order});

                update_dashboard(true, true, false);
            });

            var $publisher_order = $('#publisher_order');

            function get_publisher_order() {
                return $publisher_order.val();
            }

            $('th.sortable', $publisher_table).live('click', function () {
                var $th = $(this);
                var order;
                _.each(STATS, function (title, stat) {
                    if($th.hasClass(stat)) {
                        order = stat;
                        $publisher_order.val(stat);
                    }
                });

                $('th.sortable', $publisher_table).removeClass('sorted');
                $('th.' + order, $publisher_table).addClass('sorted');

                record_metric('Sorted publisher table', {dimension: order});

                update_dashboard(true, false, true);
            });


            /* Tables */
            function update_advertiser_colors() {
                $('tr', $advertiser_table).removeAttr('style');
                if(advertiser_comparison_shown()) {
                    $('tr.selected', $advertiser_table).each(function (index, tr) {
                        $(tr).css('background-color', COLOR_THEME.primary[index]);
                    });
                }
            }

            function update_publisher_colors() {
                $('tr', $publisher_table).removeAttr('style');
                if(publisher_comparison_shown()) {
                    $('tr.selected', $publisher_table).each(function (index, tr) {
                        $(tr).css('background-color', COLOR_THEME.primary[index]);
                    });
                }
            }

            // select sources
            $('tbody tr.source', $advertiser_table).live('click', function () {
                $(this).toggleClass('selected');

                if(advertiser_comparison_shown()) {
                    update_advertiser_colors();
                }
                else {
                    // select or deselect this source's campaigns
                    if($(this).hasClass('selected')) {
                        $(this).nextUntil('.source').addClass('selected');
                    }
                    else{
                        $(this).nextUntil('.source').removeClass('selected');
                    }

                    // hide unselected rows' stats
                    if($('tbody tr.selected', $advertiser_table).length === 0) {
                        $('tbody tr td.stat span, tbody tr td.delta span', $advertiser_table).show();
                    }
                    else {
                        $('tbody tr', $advertiser_table).each(function () {
                            $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                        });
                    }
                }

                record_metric("Selected source(s)", {});

                update_dashboard(true, false, true);
            });

            // select campaigns
            $('tbody tr.campaign', $advertiser_table).live('click', function () {
                $(this).toggleClass('selected');

                if(advertiser_comparison_shown()) {
                    update_advertiser_colors();
                }
                else {
                    // TODO: there has to be a better way to select this...
                    var $source = $(this).prev();
                    while(!$source.hasClass('source')) {
                        $source = $source.prev();
                    }
                    if($(this).hasClass('selected')) {
                        var selected = true;
                        $source.nextUntil('.source').each(function () {
                            if(!$(this).hasClass('selected')) {
                                selected = false;
                            }
                        });
                        if(selected) {
                            $source.addClass('selected');
                        }
                        else {
                            $source.removeClass('selected');
                        }
                    }
                    else {
                        $source.removeClass('selected');
                    }

                    // hide unselected rows' stats
                    if($('tbody tr.selected', $advertiser_table).length === 0) {
                        $('tbody tr td.stat span, tbody tr td.delta span', $advertiser_table).show();
                    }
                    else {
                        $('tbody tr', $advertiser_table).each(function () {
                            $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                        });
                    }
                }

                update_dashboard(true, false, true);
            });

            // select apps
            $('tbody tr.app', $publisher_table).live('click', function () {
                $(this).toggleClass('selected');

                if(publisher_comparison_shown()) {
                    update_publisher_colors();
                }
                else {
                    // select or deselect this source's campaigns
                    if($(this).hasClass('selected')) {
                        $(this).nextUntil('.app').addClass('selected');
                    }
                    else{
                        $(this).nextUntil('.app').removeClass('selected');
                    }

                    // hide unselected rows' stats
                    if($('tbody tr.selected', $publisher_table).length === 0) {
                        $('tbody tr td.stat span, tbody tr td.delta span', $publisher_table).show();
                    }
                    else {
                        $('tbody tr', $publisher_table).each(function () {
                            $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                        });
                    }
                }

                update_dashboard(true, true, false);
            });

            // select adunits
            $('tbody tr.adunit', $publisher_table).live('click', function () {
                $(this).toggleClass('selected');

                if(publisher_comparison_shown()) {
                    update_publisher_colors();
                }
                else {
                    // TODO: there has to be a better way to select this...
                    $app = $(this).prev();
                    while(!$app.hasClass('app')) {
                        $app = $app.prev();
                    }
                    if($(this).hasClass('selected')) {
                        var selected = true;
                        $app.nextUntil('.app').each(function () {
                            if(!$(this).hasClass('selected')) {
                                selected = false;
                            }
                        });
                        if(selected) {
                            $app.addClass('selected');
                        }
                        else {
                            $app.removeClass('selected');
                        }
                    }
                    else {
                        $app.removeClass('selected');
                    }

                    // hide unselected rows' stats
                    if($('tbody tr.selected', $publisher_table).length === 0) {
                        $('tbody tr td.stat span, tbody tr td.delta span', $publisher_table).show();
                    }
                    else {
                        $('tbody tr', $publisher_table).each(function () {
                            $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                        });
                    }
                }

                update_dashboard(true, true, false);
            });


            /* Rows */
            var $advertiser_rows = $('#advertiser_rows');

            function advertiser_rows_shown() {
                return $advertiser_rows.hasClass('hide');
            }

            $advertiser_rows.click(function () {
                if(advertiser_rows_shown()) {
                    $advertiser_rows.addClass('hide');
                    $advertiser_rows.removeClass('show');

                    $('tr', $advertiser_table).show();

                    record_metric('Showed advertiser rows');
                }
                else {
                    $advertiser_rows.addClass('show');
                    $advertiser_rows.removeClass('hide');

                    $('tr.hide', $advertiser_table).hide();

                    record_metric('Hid advertiser rows');
                }
            });

            var $publisher_rows = $('#publisher_rows');

            function publisher_rows_shown() {
                return $publisher_rows.hasClass('hide');
            }

            $publisher_rows.click(function () {
                if(publisher_rows_shown()) {
                    $publisher_rows.addClass('hide');
                    $publisher_rows.removeClass('show');

                    $('tr', $publisher_table).show();

                    record_metric('Showed publisher rows');
                }
                else {
                    $publisher_rows.addClass('show');
                    $publisher_rows.removeClass('hide');

                    $('tr.hide', $publisher_table).hide();

                    record_metric('Hid publisher rows');
                }
            });


            /**
             * SETUP
             */

            /* Tables */
            var filter_header_row = _.template($('#filter_header_row').html());
            $('thead', $advertiser_table).html(filter_header_row({
                title: 'Campaigns and AdGroups',
                columns: ADVERTISER_COLUMNS,
                default_columns: ADVERTISER_DEFAULT_COLUMNS,
                sortable_columns: SORTABLE_COLUMNS,
                sorted: get_advertiser_order(),
                stats: STATS
            }));

            $('thead', $publisher_table).html(filter_header_row({
                title: 'Apps and AdUnits',
                columns: PUBLISHER_COLUMNS,
                default_columns: PUBLISHER_DEFAULT_COLUMNS,
                sortable_columns: SORTABLE_COLUMNS,
                sorted: get_publisher_order(),
                stats: STATS
            }));


            /* Controls */
            $('#vs_start_end_label').val('None');

            $('#last_7_days').click();

            var valid_date_range = {
                endDate: "0d"
            };
            $('#custom_start').datepicker(valid_date_range);
            $('#custom_end').datepicker(valid_date_range);
        }
    };

    window.DashboardController = DashboardController;
    window.DashboardHelpers = DashboardHelpers;

})(this.jQuery, this.Backbone, this._);
