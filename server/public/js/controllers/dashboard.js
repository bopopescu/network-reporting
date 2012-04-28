// Load the mopub global.
// **REFACTOR**: modularization
var mopub = mopub || {};

(function($, Backbone, _){

    /*
     * ## Settings
     * Define global settings that are used throughout the module.
     */

    var DEBUG = ('' + window.location).indexOf('localhost') !== -1;

    // the origin for the stats service
    var LOCAL_STATS_SERVICE_URL = 'http://localhost:8888/';
    var STATS_SERVICE_URL = 'http://ec2-23-22-32-218.compute-1.amazonaws.com/';
    var URL = DEBUG ? LOCAL_STATS_SERVICE_URL : STATS_SERVICE_URL;

    // Color theme for the charts and table rows.
    var COLOR_THEME = {
        primary: [
            'hsla(180, 50%, 50%, 0.1)',
            'hsla(120, 50%, 50%, 0.1)',
            'hsla(60, 50%, 50%, 0.1)',
            'hsla(0, 50%, 50%, 0.1)',
            'hsla(300, 50%, 50%, 0.1)',
            'hsla(240, 50%, 50%, 0.1)'
        ],
        secondary: [
            'hsla(180, 50%, 50%, 1)',
            'hsla(120, 50%, 50%, 1)',
            'hsla(60, 50%, 50%, 1)',
            'hsla(0, 50%, 50%, 1)',
            'hsla(300, 50%, 50%, 1)',
            'hsla(240, 50%, 50%, 1)'
        ]
    };

    var MAX_COMPARISONS = COLOR_THEME.primary.length;

    // Map of property name to it's title
    var STATS = {
        'attempts': 'Att.',
        'clk': 'Clk.',
        'conv': 'Cnv.',
        'conv_rate': 'Cnv Rate',
        'cpm': 'CPM',
        'ctr': 'CTR',
        'fill_rate': 'Fill Rate',
        'imp': 'Imp.',
        'req': 'Req.',
        'rev': 'Rev.'
    };

    // Columns to display when the advertiser table has been expanded.
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

    // Columns to display when the advertiser table is first loaded,
    // before expansion.
    var ADVERTISER_DEFAULT_COLUMNS = [
        'rev',
        'imp',
        'clk'
    ];

    // Columns to display when the publisher table has been expanded.
    var PUBLISHER_COLUMNS = [
        'rev',
        'imp',
        'clk',
        'ctr',
        'cpm',
        'conv',
        'conv_rate',
        'fill_rate',
        'req'
    ];

    // Columns to display when the publisher table is first loaded,
    // before expansion.
    var PUBLISHER_DEFAULT_COLUMNS = [
        'rev',
        'imp',
        'clk'
    ];

    // Columns that can be sorted on in either table.
    var SORTABLE_COLUMNS = [
        'attempts',
        'clk',
        'conv',
        'imp',
        'req',
        'rev'
    ];

    // Max number of rows to display per model on page load,
    // before either table has been expanded.
    var MAX_CAMPAIGNS = 6;
    var MAX_APPS = 12;
    var MAX_ADUNITS = 6;

    // Width and height of the charts.
    // *Note:* these are kept in the CSS as well. They'll also
    // need to be changed if you want to adjust the chart size.
    var WIDTH = 400;
    var HEIGHT = 125;


    /*
     * ## Helper functions
     */

     // Pops up a growl-style message when something has
     // gone wrong fetching data. Use this to catch 500/503
     // errors from the server.
    var toast_error = function () {
        var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };


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


    // Gets a date string (MM/DD) from a datapoint object with a
    // stringified date or hour field (like the one we'd get
    // in a response from the stats service).
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



    // Formats a number for display based on a property name.
    // Currency will get a $, percentages will get a %. All numbers
    // will be formatted with commas and KMBT.
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


    // Formats a number in KMBT (thousands, millions,
    // billions, trillions) formatting.
    // Example: 1000000 -> 1M, 1230000000 -> 12.3B
    function format_kmbt(number, with_decimal) {

        if (with_decimal === undefined) {
            with_decimal = false;
        }

        // Numbers greater than this are ridiculous and
        // so we aren't supporting their existance.
        if (number > 999999999999999.999) {
            return number;
        }

        // Qd/Qn/Sx are there for when our customers are making
        // this much money in the future.
        var endings = ['', 'K', 'M', 'B', 'T', 'Qd', 'Qn', 'Sx'];

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

    function format_kmbt(number) {
        if(number < 1) {
            return number.toPrecision(3);
        }
        var endings = ['', 'K', 'M', 'B', 'T', 'Qd', 'Qn', 'Sx'];
        var place = Math.floor(Math.floor(Math.log(number)/Math.log(10))/3);
        var result = (number / Math.pow(1000, place)).toPrecision(3) + endings[place];
        return result;
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


    // Pads an integer <10 with a 0 on the left. Used for making dates.
    function pad(integer) {
        return integer < 10 ? '0' + integer : integer;
    }

    // Converts a string date to a javascript date object.
    function string_to_date(date_string) {
        var parts = date_string.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }


    // Converts a javascript date object to a string in the format we
    // like, "YYYY-MM-DD"
    function date_to_string(date) {
        return date.getFullYear() + '-' +
            (date.getMonth() + 1) + '-' +
            date.getDate();
    }


    // Converts a pretty date string ("03/08/1987") to a javascript
    // date object.
    function pretty_string_to_date(date_string) {
        var parts = date_string.split('/');
        return new Date(parts[2], parts[0] - 1, parts[1]);
    }


    // Converts a javascript date object to a pretty date string
    // e.g.  ("03/08/1987")
    function date_to_pretty_string(date) {
        return pad(date.getMonth() + 1) + '/' + pad(date.getDate()) + '/' + date.getFullYear();
    }


    // Converts a date hour string ("03-08-1987-13") to a javascript
    // date object.
    function string_to_date_hour(date_string) {
        var parts = date_string.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2], parts[3]);
    }


    // Converts a javascript date object to a date hour string.
    // e.g. "2012-10-29-22"
    function date_hour_to_string(date) {
        return date.getFullYear() +
            '-' + (date.getMonth() + 1) +
            '-' + date.getDate() +
            '-' + date.getHours();
    }

    // obvious
    function get_today() {
        var now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }


    /*
     * ## Chart creation
     */

    // Returns a list of the charts that we're going to display.
    // Right now this just returns a hard-coded list, but in the
    // future this could come from user defined settings that are
    // stored in a cookie.
    function get_charts() {
        return ['rev', 'imp', 'clk', 'ctr'];
    }

    // Create a new chart using Rickshaw/d3.
    // `series` is the type of series we're representing (e.g. 'rev',
    // 'imp', 'clk') and is used for formatting axes and tooltips.
    // `element` is the name of the element (e.g. '#chart') to render
    // the chart in. The chart will be rendered when the function is
    // called.
    // `account_data` is all of the data you get back from a query.
    // `options` is not currently used, but will be used in the future
    // to specify stuff like height, width, and other rendering options.
    function createChart(series, element, account_data, options) {
        var all_chart_data = _.map(account_data, function(range, i){
            var stroke;
            var color;
            if(range.id === 'vs') {
                stroke = 'hsla(0, 0%, 75%, 1)';
                color = 'hsla(0, 0%, 75%, 0.1)';
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

        // If the graph has few points, make the graph rigid.
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
        date_to_string: date_to_string
    };


    /*
     * ## Dashboard controller
     */

    var DashboardController = {
        initializeDashboard: function(bootstrapping_data) {
            var handshake_data = $.cookie('handshake_data');
            var handshake_iv = $.cookie('handshake_iv');

            var $advertiser_table = $('#advertiser');
            var $publisher_table = $('#publisher');

            // Set up JSONP for accessing data from the stats services.
            // We calculate derivative stats (ctr, fill, conversion
            // rate, etc) upon every query response for all datapoints.
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
                url: URL + 'stats/'
            });

            // Looks at the publisher or advertiser table rows that
            // have been selected and pulls out the corresponding
            // object id's. This is often used for getting a list of
            // id's to query for.  `type` is one of: `'source'`,
            // `'campaign'`, `'app'`, `'adunit'`
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


            /*
             * ## Templating
             */
            var filter_body_row = _.template($('#filter_body_row').html());
            var names = bootstrapping_data.names;

            function render_filter_body_row(context, stats, vs_stats) {
                context.name = names[context.id];

                context.stats = [];
                _.each(context.columns, function (column) {
                    context.stats[column] = format_stat(column, stats[column]);
                });

                if(typeof(vs_stats) !== 'undefined') {
                    context.deltas = {};
                    _.each(context.columns, function (column) {
                        if(vs_stats[column] === 0) {
                            context.deltas[column] = {
                                'class': '',
                                'value': ''
                            };
                        }
                        else {
                            var delta = Math.round(100 * (stats[column] - vs_stats[column]) / vs_stats[column]);
                            if(delta === 0) {
                                context.deltas[column] = {
                                    'class': '',
                                    'value': '~0%'
                                };
                            }
                            else if(delta < 0) {
                                context.deltas[column] = {
                                    'class': 'negative',
                                    'value': delta + '%'
                                };
                            }
                            else {
                                context.deltas[column] = {
                                    'class': 'positive',
                                    'value': '+' + delta + '%'
                                };
                            }
                        }
                    });
                }

                return filter_body_row(context);
            }

            function get_data() {
                var data = {
                    account: bootstrapping_data['account'],
                    handshake_data: handshake_data,
                    handshake_iv: handshake_iv,
                    start: $('#start').val(),
                    end: $('#end').val()
                };

                if($('#vs_start').val() && $('#vs_end').val()) {
                    data['vs_start'] = $('#vs_start').val();
                    data['vs_end'] = $('#vs_end').val();
                }

                return data;
            }

            function update_dashboard(update_rollups_and_charts, advertiser_table, publisher_table) {
                var data = get_data();
                var advertiser_query = get_advertiser_query();
                var publisher_query = get_publisher_query();

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
                        $('tr.selected', $advertiser_table).each(function (index, tr) {
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
                            },
                            url: URL + 'stats/'
                        });
                    } else if(publisher_comparison_shown()) {
                        $('tr.selected', $publisher_table).each(function (index, tr) {
                            var query = _.clone(advertiser_query);
                            if($(tr).hasClass('app')) {
                                query.app = [tr.id];
                            }
                            else {
                                query.adunit = [tr.id];
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
                            },
                            url: URL + 'stats/'
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
                            },
                            url: URL + 'stats/'
                        });
                    }
                }

                if (advertiser_table) {
                    update_advertiser_table(data, publisher_query);
                }

                if (publisher_table) {
                    update_publisher_table(data, advertiser_query);
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

            /*
             * ## Tables
             */
            function update_advertiser_table(data, publisher_query) {
                var selected = _.map($('tr.selected', $advertiser_table), function (tr) { return tr.id; });
                var order = get_advertiser_order();

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
                            $('tr.campaign', $advertiser_table).remove();
                            _.each(source_data.query, function(query, index) {
                                var id = query.source[0];
                                var context = {
                                    type: 'source',
                                    selected: _.include(selected, id),
                                    hidden: false,
                                    id: id,
                                    columns: ADVERTISER_COLUMNS,
                                    default_columns: ADVERTISER_DEFAULT_COLUMNS,
                                    order: order
                                };
                                var stats = json.sum[index];
                                var vs_stats;
                                if(json.vs_sum.length) {
                                    vs_stats = json.vs_sum[index];
                                }
                                $source = $(render_filter_body_row(context, stats, vs_stats));
                                if(advertiser_comparison_shown()) {
                                    $source.css('background-color', COLOR_THEME.primary[selected.indexOf(id)]);
                                }
                                if($('#' + context.id).length) {
                                    $('#' + context.id).replaceWith($source);
                                }
                                else {
                                    $advertiser_table.append($source);
                                }
                            });
                            update_campaigns(data, publisher_query, selected, order);
                        });
                    },
                    url: URL + 'stats/'
                });
            }

            function update_campaigns(data, publisher_query, selected, order) {
                _.each(['direct', 'network'], function (source) {
                    var campaign_data = _.clone(data);
                    campaign_data.granularity = 'top';
                    campaign_data.query = [_.extend(_.clone(publisher_query), {
                        source: [source],
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
                                var $last = $('#' + source);
                                _.each(json.top[0], function(top, index) {
                                    var id = top.campaign;
                                    var hidden = index >= MAX_CAMPAIGNS;
                                    var context = {
                                        type: 'campaign',
                                        selected: _.include(selected, id) || (!advertiser_comparison_shown() && _.include(selected, source)),
                                        hidden: hidden,
                                        id: id,
                                        columns: ADVERTISER_COLUMNS,
                                        default_columns: ADVERTISER_DEFAULT_COLUMNS,
                                        order: order
                                    };
                                    var stats = json.top[0][index];
                                    var vs_stats;
                                    if(json.vs_top.length && json.vs_top[0].length) {
                                        vs_stats = json.vs_top[0][index];
                                    }
                                    var $campaign = $(render_filter_body_row(context, stats, vs_stats));
                                    if(advertiser_comparison_shown()) {
                                        $campaign.css('background-color', COLOR_THEME.primary[selected.indexOf(id)]);
                                    }
                                    $last.after($campaign);
                                    $last = $campaign;
                                });

                                update_advertiser_stats_display();

                                if(advertiser_columns_shown()) {
                                    show_advertiser_columns();
                                }
                                else {
                                    hide_advertiser_columns();
                                }

                                if(advertiser_rows_shown()) {
                                    show_advertiser_rows();
                                }
                                else {
                                    hide_advertiser_rows();
                                }
                            });
                        },
                        url: URL + 'topN/'
                    });
                });
            }

            function update_publisher_table(data, advertiser_query) {
                selected = _.map($('tr.selected', $publisher_table), function (tr) { return tr.id; });
                var order = get_publisher_order();

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
                            $('tr.app, tr.adunit', $publisher_table).remove();
                            _.each(json.top[0], function (top, index) {
                                var id = top.app;
                                var context = {
                                    type: 'app',
                                    selected: _.include(selected, id),
                                    hidden: index >= MAX_APPS,
                                    id: id,
                                    columns: PUBLISHER_COLUMNS,
                                    default_columns: PUBLISHER_DEFAULT_COLUMNS,
                                    order: order
                                };
                                var stats = json.top[0][index];
                                var vs_stats;
                                if(json.vs_top.length && json.vs_top[0].length) {
                                    vs_stats = json.vs_top[0][index];
                                }
                                var $app = $(render_filter_body_row(context, stats, vs_stats));
                                if(publisher_comparison_shown()) {
                                    $app.css('background-color', COLOR_THEME.primary[selected.indexOf(id)]);
                                }
                                $publisher_table.append($app);
                            });
                            update_adunits(data, advertiser_query, selected, order);
                        });
                    },
                    url: URL + 'topN/'
                });
            }

            function update_adunits(data, advertiser_query, selected, order) {
                $('tr.app', $publisher_table).each(function () {
                    var app = this.id;

                    var adunit_data = _.clone(data);
                    adunit_data.granularity = 'top';
                    adunit_data.query = [_.extend(_.clone(advertiser_query), {
                        app: [app],
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
                                var $last = $('#' + app);
                                _.each(json.top[0], function(top, index) {
                                    var id = top.adunit;
                                    var context = {
                                        type: 'adunit',
                                        selected: _.include(selected, id) || (!publisher_comparison_shown() && _.include(selected, app)),
                                        hidden: index >= MAX_ADUNITS,
                                        id: id,
                                        columns: PUBLISHER_COLUMNS,
                                        default_columns: PUBLISHER_DEFAULT_COLUMNS,
                                        order: order
                                    };
                                    var stats = json.top[0][index];
                                    var vs_stats;
                                    if(json.vs_top.length && json.vs_top[0].length) {
                                        vs_stats = json.vs_top[0][index];
                                    }
                                    var $adunit = $(render_filter_body_row(context, stats, vs_stats));
                                    if(publisher_comparison_shown()) {
                                        $adunit.css('background-color', COLOR_THEME.primary[selected.indexOf(id)]);
                                    }
                                    $last.after($adunit);
                                    $last = $adunit;
                                });

                                update_publisher_stats_display();

                                if(publisher_columns_shown()) {
                                    show_publisher_columns();
                                }
                                else {
                                    hide_publisher_columns();
                                }

                                if(publisher_rows_shown()) {
                                    show_publisher_rows();
                                }
                                else {
                                    hide_publisher_rows();
                                }
                            });
                        },
                        url: URL + 'topN/'
                    });
                });
            }


            /* Date Range */

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

            // default start/end
            update_start_end('last_14_days');

            var valid_date_range = {
                endDate: "0d"
            };
            $('#custom_start').datepicker(valid_date_range);
            $('#custom_end').datepicker(valid_date_range);


            /* Comparison Date Range */
            function update_vs_start_end(vs_start_end) {
                if(vs_start_end == 'none') {
                    $('#vs_start').val('');
                    $('#vs_end').val('');
                    $('#vs_start_end_label').html('None');
                }
                else {
                    if(advertiser_comparison_shown()) {
                        hide_advertiser_comparison();
                    }
                    if(publisher_comparison_shown()) {
                        hide_publisher_comparison();
                    }

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
            }

            function hide_advertiser_comparison() {
                $advertiser_comparison.addClass('show');
                $advertiser_comparison.removeClass('hide');

                // default no comparison selection: none
                $('tbody tr', $advertiser_table).removeClass('selected');
            }

            $advertiser_comparison.click(function () {
                if(advertiser_comparison_shown()) {
                    hide_advertiser_comparison();
                }
                else {
                    update_vs_start_end('none');
                    if(publisher_comparison_shown()) {
                        hide_publisher_comparison();
                    }
                    show_advertiser_comparison();
                }

                update_advertiser_colors();

                update_advertiser_stats_display();

                update_dashboard(true, false, true);
            });

            var $publisher_comparison = $('#publisher_comparison');

            function publisher_comparison_shown() {
                return $publisher_comparison.hasClass('hide');
            }

            function show_publisher_comparison() {
                $publisher_comparison.addClass('hide');
                $publisher_comparison.removeClass('show');

                // default comparison selection: all apps
                $('tr.app', $publisher_table).slice(0, MAX_CAMPAIGNS).addClass('selected');
                $('tr.adunit', $publisher_table).removeClass('selected');
            }

            function hide_publisher_comparison() {
                $publisher_comparison.addClass('show');
                $publisher_comparison.removeClass('hide');

                // default no comparison selection: none
                $('tbody tr', $publisher_table).removeClass('selected');
            }

            $publisher_comparison.click(function () {
                if(publisher_comparison_shown()) {
                    hide_publisher_comparison();
                }
                else {
                    update_vs_start_end('none');
                    if(advertiser_comparison_shown()) {
                        hide_advertiser_comparison();
                    }
                    show_publisher_comparison();
                }

                update_publisher_colors();

                update_publisher_stats_display();

                update_dashboard(true, true, false);
            });

            /* Columns */
            var $advertiser_columns = $('#advertiser_columns');

            function advertiser_columns_shown() {
                return $advertiser_columns.hasClass('hide');
            }

            function show_advertiser_columns() {
                $('#publisher_filters').hide();
                $('#advertiser_filters').addClass('expand');
                $('th, td', $advertiser_table).show();
            }

            function hide_advertiser_columns() {
                var order = get_advertiser_order();
                _.each(ADVERTISER_COLUMNS, function (column) {
                    if(!_.include(ADVERTISER_DEFAULT_COLUMNS, column) && column !== order) {
                        $('th.' + column + ', td.' + column, $advertiser_table).hide();
                    }
                });
                $('#advertiser_filters').removeClass('expand');
                $('#publisher_filters').show();
            }

            $advertiser_columns.click(function () {
                if(advertiser_columns_shown()) {
                    $advertiser_columns.addClass('show');
                    $advertiser_columns.removeClass('hide');

                    hide_advertiser_columns();

                    record_metric('Hid advertiser columns');
                }
                else {
                    $advertiser_columns.addClass('hide');
                    $advertiser_columns.removeClass('show');

                    show_advertiser_columns();

                    record_metric('Showed advertiser columns');
                }
            });

            var $publisher_columns = $('#publisher_columns');

            function publisher_columns_shown() {
                return $publisher_columns.hasClass('hide');
            }

            function show_publisher_columns() {
                $('#advertiser_filters').hide();
                $('#publisher_filters').addClass('expand');
                $('th, td', $publisher_table).show();
            }

            function hide_publisher_columns() {
                var order = get_publisher_order();
                _.each(PUBLISHER_COLUMNS, function (column) {
                    if(!_.include(PUBLISHER_DEFAULT_COLUMNS, column) && column !== order) {
                        $('th.' + column + ', td.' + column, $publisher_table).hide();
                    }
                });
                $('#publisher_filters').removeClass('expand');
                $('#advertiser_filters').show();
            }

            $publisher_columns.click(function () {
                if(publisher_columns_shown()) {
                    $publisher_columns.addClass('show');
                    $publisher_columns.removeClass('hide');

                    hide_publisher_columns();

                    record_metric('Hid publisher columns');
                }
                else {
                    $publisher_columns.addClass('hide');
                    $publisher_columns.removeClass('show');

                    show_publisher_columns();

                    record_metric('Showed publisher columns');
                }
            });


            /* Order */
            var $advertiser_order = $('#advertiser_order');

            function get_advertiser_order() {
                return $advertiser_order.val();
            }

            var filter_header_row = _.template($('#filter_header_row').html());
            $('thead', $advertiser_table).html(filter_header_row({
                title: 'Ads',
                columns: ADVERTISER_COLUMNS,
                default_columns: ADVERTISER_DEFAULT_COLUMNS,
                sortable_columns: SORTABLE_COLUMNS,
                sorted: get_advertiser_order(),
                stats: STATS
            }));

            $('th.orderable', $advertiser_table).click(function () {
                var $th = $(this);
                var order;
                _.each(STATS, function (title, stat) {
                    if($th.hasClass(stat)) {
                        order = stat;
                        $advertiser_order.val(stat);
                    }
                });

                $('th.orderable', $advertiser_table).removeClass('ordered');
                $('th.' + order, $advertiser_table).addClass('ordered');

                record_metric('Ordered advertiser table', {dimension: order});

                update_dashboard(false, true, false);
            });

            var $publisher_order = $('#publisher_order');

            function get_publisher_order() {
                return $publisher_order.val();
            }

            $('thead', $publisher_table).html(filter_header_row({
                title: 'Apps',
                columns: PUBLISHER_COLUMNS,
                default_columns: PUBLISHER_DEFAULT_COLUMNS,
                sortable_columns: SORTABLE_COLUMNS,
                sorted: get_publisher_order(),
                stats: STATS
            }));

            $('th.orderable', $publisher_table).click(function () {
                var $th = $(this);
                var order;
                _.each(STATS, function (title, stat) {
                    if($th.hasClass(stat)) {
                        order = stat;
                        $publisher_order.val(stat);
                    }
                });

                $('th.orderable', $publisher_table).removeClass('ordered');
                $('th.' + order, $publisher_table).addClass('ordered');

                record_metric('Ordered publisher table', {dimension: order});

                update_dashboard(false, false, true);
            });


            /* Tables */
            /* TODO: refactor, reorganize */
            function update_advertiser_colors() {
                if(advertiser_comparison_shown()) {
                    $('tr', $advertiser_table).not('.selected').css('background-color', 'inherit');
                    $('tr.selected', $advertiser_table).each(function (index, tr) {
                        $(tr).css('background-color', COLOR_THEME.primary[index]);
                    });
                }
                else {
                    $('tr', $advertiser_table).css('background-color', 'inherit');
                }
            }

            function get_advertiser_query() {
                if($('tr.selected', $advertiser_table).length === 0) {
                    return {};
                }

                var use_source = true;
                $('tr.source', $advertiser_table).each(function (index, source) {
                    if(!$(source).hasClass('selected')) {
                        $(source).nextUntil('tr.source').each(function (index, campaign) {
                            if($(campaign).hasClass('selected')) {
                                use_source = false;
                            }
                        });
                    }
                });
                if(use_source) {
                    return { source: get_keys('source') };
                }

                return { campaign: get_keys('campaign') };
            }

            function update_advertiser_stats_display() {
                if($('tr.selected', $advertiser_table).length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', $advertiser_table).show();
                }
                else {
                    $('tbody tr', $advertiser_table).each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }
            }

            // select sources
            $('tbody tr.source', $advertiser_table).live('click', function () {
                var $source = $(this);
                $source.toggleClass('selected');

                if(advertiser_comparison_shown()) {
                    // TODO: make sure not more than MAX_COMPARISONS
                    update_advertiser_colors();
                }
                else {
                    // select or deselect this source's campaigns
                    if($source.hasClass('selected')) {
                        $source.nextUntil('.source').addClass('selected');
                    }
                    else{
                        $source.nextUntil('.source').removeClass('selected');
                    }
                }

                // TODO: only need to update this row
                update_advertiser_stats_display();

                record_metric("Selected source(s)", {});

                update_dashboard(true, false, true);
            });

            // select campaigns
            $('tbody tr.campaign', $advertiser_table).live('click', function () {
                var $campaign = $(this);
                $campaign.toggleClass('selected');

                if(advertiser_comparison_shown()) {
                    // TODO: make sure not more than MAX_COMPARISONS
                    update_advertiser_colors();
                }
                else {
                    // TODO: there has to be a better way to select this...
                    var $source = $campaign.prev();
                    while(!$source.hasClass('source')) {
                        $source = $source.prev();
                    }
                    if($campaign.hasClass('selected')) {
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
                }

                // TODO: only need to update this row
                update_advertiser_stats_display();

                record_metric("Selected campaign(s)", {});

                update_dashboard(true, false, true);
            });

            function update_publisher_colors() {
                $('tr', $publisher_table).removeAttr('style');
                if(publisher_comparison_shown()) {
                    $('tr.selected', $publisher_table).each(function (index, tr) {
                        $(tr).css('background-color', COLOR_THEME.primary[index]);
                    });
                }
            }

            function get_publisher_query() {
                if($('tr.selected', $publisher_table).length === 0) {
                    return {};
                }

                var use_app = true;
                $('tr.app', $publisher_table).each(function (index, app) {
                    if(!$(app).hasClass('selected')) {
                        $(app).nextUntil('tr.app').each(function (index, adunit) {
                            if($(adunit).hasClass('selected')) {
                                use_app = false;
                            }
                        });
                    }
                });
                if(use_app) {
                    return { app: get_keys('app') };
                }

                return { adunit: get_keys('adunit') };
            }

            function update_publisher_stats_display() {
                if($('tr.selected', $publisher_table).length === 0) {
                    $('tbody tr td.stat span, tbody tr td.delta span', $publisher_table).show();
                }
                else {
                    $('tbody tr', $publisher_table).each(function () {
                        $('td.stat span, td.delta span', this).toggle($(this).hasClass('selected'));
                    });
                }
            }

            // select apps
            $('tbody tr.app', $publisher_table).live('click', function () {
                $(this).toggleClass('selected');

                if(publisher_comparison_shown()) {
                    // TODO: make sure not more than MAX_COMPARISONS
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
                    // TODO: make sure not more than MAX_COMPARISONS
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

            function show_advertiser_rows() {
                $('tr', $advertiser_table).show();
            }

            function hide_advertiser_rows() {
                $('tbody tr', $advertiser_table).each(function () {
                    $tr = $(this);
                    $tr.toggle(!$tr.hasClass('hidden') || $tr.hasClass('selected'));
                });
            }

            $advertiser_rows.click(function () {
                if(advertiser_rows_shown()) {
                    $advertiser_rows.addClass('show');
                    $advertiser_rows.removeClass('hide');

                    hide_advertiser_rows();

                    record_metric('Hid advertiser rows');
                }
                else {
                    $advertiser_rows.addClass('hide');
                    $advertiser_rows.removeClass('show');

                    show_advertiser_rows();

                    record_metric('Showed advertiser rows');
                }
            });

            var $publisher_rows = $('#publisher_rows');

            function publisher_rows_shown() {
                return $publisher_rows.hasClass('hide');
            }

            function show_publisher_rows() {
                $('tr', $publisher_table).show();
            }

            function hide_publisher_rows() {
                $('tbody tr', $publisher_table).each(function () {
                    $tr = $(this);
                    $tr.toggle(!$tr.hasClass('hidden') || $tr.hasClass('selected'));
                });
            }

            $publisher_rows.click(function () {
                if(publisher_rows_shown()) {
                    $publisher_rows.addClass('show');
                    $publisher_rows.removeClass('hide');

                    hide_publisher_rows();

                    record_metric('Hid publisher rows');
                }
                else {
                    $publisher_rows.addClass('hide');
                    $publisher_rows.removeClass('show');

                    show_publisher_rows();

                    record_metric('Showed publisher rows');
                }
            });

            update_dashboard(true, true, true);
        }
    };

    window.DashboardController = DashboardController;
    window.DashboardHelpers = DashboardHelpers;

})(this.jQuery, this.Backbone, this._);
