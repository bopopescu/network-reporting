/*
 * # MoPub Global JS
 */


/*
 * Make sure there's a console.log function in case we forgot to remove debug statements
 */
if (window.console === undefined) {
    window.console = {
        log: function() {}
    };
}

/*
 * # Global document.ready function
 * If you want something to happen everywhere, on every page,
 * it should go here.
 */
(function($) {
    
    var mopub = window.mopub || {};
    var Chart = mopub.Chart || {};
    var Stats = mopub.Stats || {};
    var Utils = mopub.Utils || {};
        

    
    /*
     * Sets up the date range buttons at the top of each page.
     * In the future, this should be refactored to use a backbone
     * router.
     */
    function initializeDateButtons () {
        
        /*
         * Utils for making the date range url params
         */
        var parse_date = function (date) {
            var d = new Date(date);
            var non_retarded_month = d.getMonth() + 1;
            return d.getFullYear() + 
                "-" + non_retarded_month + 
                "-" + d.getDate();
        };

        /*
         * Get the number of days between start and end.
         * Not inclusive of the start date. 
         */
        var days_between = function (start, end) {
            
            // cast, in case they passed in strings
            var start_date = new Date(start);
            var end_date = new Date(end);            

            var daylight_savings_adjust = 0;

            // constants used for our calculations below
            var one_minute = 1000 * 60;
            var one_day = one_minute * 60 * 24;

            // equalize times in case date objects have them
            start_date.setHours(0);
            start_date.setMinutes(0);
            start_date.setSeconds(0);
            end_date.setHours(0);
            end_date.setMinutes(0);
            end_date.setSeconds(0);

            // take care of spans across Daylight Saving Time changes
            if (end_date > start_date) {
                daylight_savings_adjust = (end_date.getTimezoneOffset() - 
                             start_date.getTimezoneOffset()) * one_minute;
            } else {
                daylight_savings_adjust = (start_date.getTimezoneOffset() -
                             end_date.getTimezoneOffset()) * one_minute;    
            }
            var diff = Math.abs(end_date.getTime() - start_date.getTime()) 
                - daylight_savings_adjust;
            return Math.ceil(diff/one_day);
        };

        /*
         * Set up the custom date range button. Dates one day later
         * than today and two months before today can't be picked.
         * When the custom button is clicked, it opens up the date
         * range picker right underneath it. 
         */

        // Set up the two date fields with datepickers
        var valid_date_range = {
            startDate: "-2m",
            endDate: "+1d"
        };
        $("input[name='start-date']").datepicker(valid_date_range);
        $("input[name='end-date']").datepicker(valid_date_range);

        // Set up the click event that opens the date range picker
        var currently_active = $("#date-range-controls .btn.active");
        var custom_controls = $("#datepicker-custom");
        custom_controls.click(function(event) {
            currently_active.toggleClass("active");
            custom_controls.toggleClass("active");            
            $("#datepicker-custom-range").toggleClass('hidden');
            $(".caret", custom_controls).toggleClass('flip-vertical');
        });

        // On submit, get the date range from the two inputs and
        // form the url, and reload the page.
        $("#custom-date-submit").click(function() {
            var start_date = $("#datepicker-start-input").val();
            var end_date = $("#datepicker-end-input").val();

            // days_between is not inclusive, we add +1 to the range
            // because the server expects inclusive.
            var date_range = days_between(start_date, end_date) + 1;
            var formatted_start_date = parse_date(start_date);

            if (date_range > 0) {
                var url_params = "?r="
                                 + date_range
                                 + "&s="
                                 + formatted_start_date;

                window.location = window.location.protocol + "//"
                    + window.location.host + window.location.pathname 
                    + url_params;
            } else {
                // handle error
            }
        });

        /*
         * The other date buttons.
         * Figure out the appropriate url parameters for the date range
         * and set up the url. On click, load that url if the button isnt
         * disabled.
         */
        _.each(['today', 'yesterday', '7', '14'], function(value) {

            var anchor = $(this);
            var url_params = "";

            // button click handler for today
            if (value === 'today') {
                var today = new Date();
                var today_string = parse_date(today);
                
                url_params = "?r=1"
                    + "&s="
                    + today_string;
            } else if (value === 'yesterday'){
                var today = new Date();
                today.setDate(today.getDate() - 1);
                var yesterday_string = parse_date(today);
                
                url_params = "?r=1"
                    + "&s="
                    + yesterday_string;
            } else {
                url_params = "?r="
                    + value;
            }

            $("#datepicker-" + value).click(function(event){
                event.preventDefault();
                if (!anchor.hasClass('disabled')){
                    window.location = window.location.protocol + "//"
                        + window.location.host + window.location.pathname 
                        + url_params;
                }
            });
        });
    }

    
    $(function() {        
        initializeDateButtons();
        
        /*
         * ## Mixpanel Event Tracking
         */

        // marketplace hiding
        if ($('#is_admin_input').val()=='False') {
            $('.marketplace').hide();
        }

        // set up validation to be run on form submit
        $('.validate').validate();

        // Tables with the 'sortable' class will be made sortable by default
        $(".sortable").tablesorter();

        $('.dropdown-toggle').dropdown();

        // Tabify tabs
        $('.tabs').tabs();
        $('.pills').tabs();


        // Override default jQuery UI dialog options
        $.extend($.ui.dialog.prototype.options, {
            modal: true,
            resizable: false,
            draggable: false,
            width: 400
        });

        // Set up form placeholders
        $('input[placeholder], textarea[placeholder]').placeholder({ 
            preventRefreshIssues: true 
        });

        // Set up text overflow elements
        $('#titlebar .breadcrumb h1, .dataTable-name .inner').textOverflow(' &hellip;');

        //REFACTOR: replace this with something from bootstrap
        $("#account-dropdown").dropdown();
        
        // Set up alert-message closing
        $(".alert-message .close").click(function() {
            $(this).parent().fadeOut();
        });

        $('.formFields-field-help-link[title]').click(function(e) { 
            e.preventDefault(); 
        });

        // Set up highcharts default options
        Highcharts.setOptions({
            chart: {
                animation: false,
                backgroundColor: null,
                borderRadius: 0,
                margin: [30,0,30,45],
                height: 185
            },
            title: { text: null },
            lang: {
                loading: "Loading ..."
            },
            credits: { enabled: false },
            style: {
                fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif'
            },
            plotOptions: {
                series: {
                    animation: false,
                    shadow: false,
                    stickyTracking: false
                },
                area: {
                    lineWidth: 4,
                    fillOpacity: 0.1,
                    stacking: 'normal',
                    marker: {
                        lineWidth: 2,
                        radius: 5,
                        symbol: 'circle',
                        states: {
                            hover: {
                                lineWidth: 2,
                                radius: 7
                            }
                        }
                    },
                    states: {
                        hover: {
                            lineWidth: 4
                        }
                    }
                }
            },
            xAxis: {
                endOnTick: false,
                gridLineWidth: 0.5,
                gridLineColor: '#dddddd',
                lineWidth: 1,
                lineColor: '#cccccc',
                type: 'datetime',
                labels: {
                    style: {
                        fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                        color: '#999',
                        fontSize: '10px'
                    },
                    y: 20
                },
                dateTimeLabelFormats: {
                    second: '%b %e %l:%M:%S%p',
                    minute: '%b %e %l:%M%p',
                    hour: '%b %e %l:%M%p',
                    day: '%b %e',
                    week: '%b %e',
                    month: '%b %Y',
                    year: '%Y'
                },
                tickColor: '#dddddd',
                tickLength: 5,
                tickWidth: 0.5
            },
            yAxis: {
                showFirstLabel: false,
                showLastLabel: true,
                gridLineWidth: 0.5,
                gridLineColor: '#dddddd',
                min: 0,
                title: {
                    text: null
                },
                labels: {
                    style: {
                        fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                        color: '#999',
                        fontSize: '10px'
                    },
                    x: -5
                }
            },
            legend: {
                borderColor: null,
                borderRadius: 0,
                borderWidth: 0,
                align: 'center',
                verticalAlign: 'top',
                y: -17,
                itemStyle: {
                    fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                    size: '12px',
                    cursor: 'pointer',
                    color: '#444444'
                },
                itemHoverStyle: {
                    color: '#e57300'
                },
                itemHiddenStyle: {
                    color: '#ccc'
                },
                lineHeight: 12,
                symbolPadding: 6,
                symbolWidth: 12
            },
            tooltip: {
                backgroundColor: "rgba(255, 255, 255, .9)",
                style: {
                    fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                    fontSize: '13px',
                    padding: '10px'
                }
            }
        });

        // Set up 'What's This?' dialogs
        $('.whatsthis').live('click', function(e) {
            e.preventDefault();
            $('#'+$(this).attr('id').replace('helpLink', 'helpContent')).dialog({
                buttons: { "Close": function() { $(this).dialog('close');} }
            });
        });


    }); // end $(document).ready

    function getUrlParameters() {
        var parameters = {};
        var url_params = window.location.search.slice(1).split('&');
        var param;
        for(var i = 0; i < url_params.length; i++)
        {
            param = url_params[i].split('=');
            parameters[param[0]] = param[1];
        }
        return parameters;
    }

    var url_parameters = getUrlParameters();



    /*
     * # MoPub-defined jQuery utility functions and extensions
     */

    /*
     * ## Image Preloader
     * Caches images for faster loading
     */
    var cache = [];
    $.preLoadImages = function() {
        var args_len = arguments.length;
        for (var i = args_len; i--;) {
            var cacheImage = document.createElement('img');
            cacheImage.src = arguments[i];
            cache.push(cacheImage);
        }
    };

    $.fn.fadeThenSlideToggle = function(speed, easing, callback) {
        if (this.is(":hidden")) {
            return this.slideDown(speed, easing).fadeTo(speed, 1, easing, callback);
        } else {
            return this.fadeTo(speed, 0, easing).slideUp(speed, easing, callback);
        }
    };
    
    /*
     * ## Activity utility functions
     */
    function isActive(item) {
        return item.hasClass('active');
    }

    function activate (element, container) {
        if (container.length > 1) {
            container.each(function(){
                $(this).removeClass('active');
            });
        } else {
            container.find('.active').removeClass('active');
        }
        element.addClass('active');
    }


    /*
     * ## Tabs
     * Turns a ul into horizontal tabs, that can be used to hide and show
     * sections of a page.
     *
     * Usage:
     * `<ul class="tabs">`
     *
     * ` <li class="active"> <a href="#s1">Section 1 </a> </li>`
     *
     * ` <li> <a href="#s2">Section 2 </a> </li>`
     *
     * `</ul>`
     *
     * `<div class="active tab-section" id="s1"></div>`
     *
     * `<div class="tab-section" id="s2"></div>`
     *
     * `$(".tabs").tabs();`
     *
     * TODO: Refactor so that the first tab/section are activated if nothing is activated by default
     */
    $.fn.tabs = function() {
        // find the sections within the page we've marked as tab activate-able
        var tab_sections = $(".tab-section");
        // bind the ul
        var ul = $(this);
        // get the <li>'s within the ul
        var list_items = $('li', ul);
        // add actions to each of the li/a clicks
        $.each(list_items, function(iter, item) {
            // prevent jumping around when a tab is clicked
            var anchor = $('a', item);
            $(anchor).click(function(event){
                event.preventDefault();
            });
            // activate the tab and its section on a click
            var href = anchor.attr('href');
            $(item).click(function(){
                activate($(this), ul);
                activate($(href), tab_sections);
                window.location.hash = href + "-tab";
            });

            if (window.location.hash == href + "-tab") {
                $(item).click();
            }
        });
    };


    /*
     * Escaping/unescaping HTML.
     *
     * Be careful: if you escape html thats already escaped, things get weird.
     */
    $.unescapeHTML = function (html) {
        return $("<div />").html(html).text();
    };

    $.escapeHTML = function (html) {
        return $("<div />").text(html).html();
    };


    /*
     * ## jQuery Lightswitch
     *
     * lightswitch takes two functions, an on function and an off function.
     * When the lightswitch in the page is clicked on or off, the the corresponding
     * function is called. If the function returns true, the switch is slid.
     *
     * Usage:
     *
     * `var on = function() {`
     *
     * `   console.log('BOOMSLAM');`
     *
     * `   return true;`
     *
     * `};`
     *
     *
     * `var off = function() {`
     *
     * `   console.log('SEE YA');`
     *
     * `   return true;`
     *
     * `};`
     *
     * `$(".lightswitch").lightswitch(on, off);`
     *
     * HTML:
     * <div class="lightswitch">
     *   <div class="switch on"></div>
     * </div>
     */
    $.fn.lightswitch = function (on_function, off_function) {

        if (typeof on_function == 'undefined') {
            on_function = function () {
                return true;
            };
        }

        if (typeof off_function == 'undefined') {
            off_function = function () {
                return true;
            };
        }

        var light_switch = $(this);
        var switcher = $('.switch', light_switch);

        light_switch.click(function () {
            if (switcher.hasClass('on')) {
                var result = off_function();
                if (result) {
                    switcher.removeClass('on').addClass('off');
                }

            } else if (switcher.hasClass('off')) {
                var result = on_function();
                if (result) {
                    switcher.removeClass('off').addClass('on');
                }
            } else {
                switcher.addClass('off');
            }
        });
    };

    $.fn.lightswitchOn = function () {
        var light_switch = $(this);
        var switcher = $('.switch', light_switch);
        switcher.removeClass('off').addClass('on');
    };

    $.fn.lightswitchOff = function () {
        var light_switch = $(this);
        var switcher = $('.switch', light_switch);
        switcher.removeClass('on').addClass('off');
    };

    mopub.Utils = mopub.Utils || {};

    /*
     * ## Mopub Utility
     */
    mopub.Utils.formatNumberWithCommas = function(string) {
        string += '';
        var x = string.split('.');
        var x1 = x[0];
        var x2 = x.length > 1 ? '.' + x[1] : '';
        var rgx = /(\d+)(\d{3})/;
        while (rgx.test(x1)) {
            var x1 = x1.replace(rgx, '$1' + ',' + '$2');
        }
        return x1 + x2;
    };

    mopub.Utils.formatCurrency = function(num) {
        return "$" + mopub.Utils.formatNumberWithCommas(num.toFixed(2));
    };

    mopub.Utils.formatNumberAsPercentage = function(string) {
        // We round to two decimal places.
        return (string*100).toFixed(2) + '%';
    };

    mopub.Utils.getKeysFromObject = function(object) {
        var keys = [];
        for (var key in object) {
            if (object.hasOwnProperty(key)) keys.push(key);
        }
        return keys;
    };

    /*
     * ## Stat sorting
     */
    Stats.sortStatsObjectsByStat = function(objects, statName) {
        objects.sort(function(a, b) {
            var statA = parseFloat(a["stats"]["sum"][statName]);
                var statB = parseFloat(b["stats"]["sum"][statName]);
            if (statA < statB) return 1;
            if (statA > statB) return -1;
            else return 0;
        });
        return objects;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.statArrayFromDailyStats = function(arrayOfDailyStats, statName) {
        return $.map(arrayOfDailyStats, function(oneDayStats) {
            return parseFloat(oneDayStats[statName]);
        });
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.getGraphSummedStatsForStatName = function(statName, objects) {
        var result = [];

        var topThreePerformers = objects.splice(0, 3);
        var otherPerformers = objects;

        // Get stats for the top three performers.
        $.each(topThreePerformers, function(index, statsObject) {
                var name = statsObject["key"];
            var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
            var graphStatsObject = {};
            graphStatsObject[name] = Stats.statArrayFromDailyStats(arrayOfDailyStats, statName);
            result.push(graphStatsObject);
        });

        if (otherPerformers.length == 0) return result;

        // Get stats for all other performers.
        var statsForOtherPerformers = Stats.sumDailyStatsAcrossStatsObjects(otherPerformers, statName);
        var otherDict = { "Others": statsForOtherPerformers };
        result.push(otherDict);

        return result;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.sumDailyStatsAcrossStatsObjects = function(objects, statName) {
        var result = [];
        $.each(objects, function(index, statsObject) {
            var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
            $.each(arrayOfDailyStats, function(dayIndex, oneDayStats) {
                if (!result[dayIndex]) result[dayIndex] = 0;
                result[dayIndex] += parseFloat(oneDayStats[statName]);
            });
        });
        return result;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.getGraphCtrStats = function(objects) {
        var result = [];

        var topThreePerformers = objects.splice(0, 3);
        var otherPerformers = objects;

        // Get stats for the top campaigns.
        $.each(topThreePerformers, function(index, statsObject) {
            var name = statsObject["key"];
            var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
            var graphStatsObject = {};
            graphStatsObject[name] = Stats.statArrayFromDailyStats(arrayOfDailyStats, "ctr");
            result.push(graphStatsObject);
        });

        if (otherPerformers.length == 0) return result;

        // Get stats for all other campaigns.
        var statsForOtherPerformers = Stats.getDailyCtrAcrossStatsObjects(otherPerformers);
        var otherDict = { "Others": statsForOtherPerformers };
        result.push(otherDict);

        return result;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.getDailyCtrAcrossStatsObjects = function(objects) {
        var ctr = [];
        var clicks = Stats.sumDailyStatsAcrossStatsObjects(objects, "click_count");
        var impressions = Stats.sumDailyStatsAcrossStatsObjects(objects, "impression_count");

        for (var i = 0, len = clicks.length; i < len; i++) {
            ctr[i] = (impressions[i] === 0) ? 0 : clicks[i] / impressions[i];
        }
        return ctr;
    };

    /*
     * ## Dashboard Stats Chart
     */

    /*
     * ## Y-Axis formating utility functions
     *
     * There are a couple of different ways to format the y-axis labels.
     * Here are a couple of utility y-axis formatting functions.
     */
    Chart.moneyLabelFormatter = function() {
        return '$' + Highcharts.numberFormat(this.value, 0);
    };

    Chart.percentageLabelFormatter = function() {
        return Highcharts.numberFormat(this.value, 0) + '%';
    };

    Chart.numberLabelFormatter = function() {
        if (this.value >= 1000000000) {
            return Highcharts.numberFormat(this.value / 1000000000, 0) + "B";
        } else if (this.value >= 1000000) {
            return Highcharts.numberFormat(this.value / 1000000, 0) + "M";
        } else if (this.value >= 1000) {
            return Highcharts.numberFormat(this.value / 1000, 0) + "K";
        } else if (this.value > 0) {
            return Highcharts.numberFormat(this.value, 0);
        } else {
            return "0";
        }
    };

    /*
     * ## Tooltip Utility functions
     *
     * Like the y-axis formatting, tooltips change depending on the type
     * of data they feature. Here are a couple of common ones.
     */
    Chart.defaultTooltipFormatter = function() {
        var value = Highcharts.numberFormat(this.y, 0);
        var total = Highcharts.numberFormat(this.total, 0);
        var text = '<span style="font-size: 14px;">'
            + Highcharts.dateFormat('%A, %B %e, %Y', this.x)
            + '</span>'
            + '<br/>'
            + '<span style="padding: 0; '
            + 'font-weight: 600; '
            + 'color: ' + this.series.color
            + '">'
            + this.series.name
            + '</span>'
            + ': <strong style="font-weight: 600;">'
            + value
            + '</strong><br/>';
        return text;
    };

    /*
     * ## Chart default options
     */
    Chart.highChartDefaultOptions = {
        chart: {
            defaultSeriesType: 'line',
            margin: [30,0,30,45]
        },
        legend: {
            verticalAlign: "bottom",
            y: -7,
            enabled: true
        },
        yAxis: {
            labels: {
                formatter: Chart.numberLabelFormatter
            }
        },
        tooltip: {
            formatter: Chart.defaultTooltipFormatter
        }
    };

    /*
     * New way of setting up a stats chart. Let's use this.
     */
    Chart.createStatsChart = function(selector, data, extraOptions) {

        // extraOptions aren't required
        if (typeof extraOptions == 'undefined') {
            extraOptions = {};
        }

        // If the data isn't formatted correctly, bring up a chart error
        if (typeof data == 'undefined') {
            Chart.chartError();
            return;
        }

        // Each data item should have a color and a line width
        var colors = ['#0090d9', '#e57300', '#53a600', '#444444', '#60beef'];
        $.each(data, function(iter, item){
            if (typeof item.color == 'undefined') {
                item.color = colors[iter % colors.length];
            }
            item.lineWidth = 4;
        });

        // Create the highcharts options from the
        var options = $.extend(Chart.highChartDefaultOptions, {
            chart: {
                renderTo: selector.replace('#','')
            },
            series: data
        });

        // setup HighCharts chart
        var highchart = new Highcharts.Chart(options);
     };


    /*
     * Old chart stuff. Depricating.
     */
    Chart.insertStatsChart = function(selector, seriesType, data) {
        var metricElement = $(selector);
    };

    Chart.setupDashboardStatsChart = function(seriesType) {
        // get active metric from breakdown
        var metricElement = $('#dashboard-stats .stats-breakdown .active');
        if (metricElement === null || metricElement.length === 0) return;
        var metricElementIdComponents = metricElement.attr('id').split('-');
        var activeMetric = metricElementIdComponents[metricElementIdComponents.length - 1];

        // get data
        var data = mopub.dashboardStatsChartData;
        if (typeof data == 'undefined') {
            Chart.chartError();
            return;
        }

        // set up series
        var colors = ['#0090d9', '#e57300', '#53a600', '#444444'];
        var chartSeries = [];
        var activeData = data[activeMetric];
        if (typeof activeData == 'undefined') {
            Chart.chartError();
            return;
        }

        $.each(activeData, function(i, seriesObject) {
            var seriesName, seriesData, seriesLineWidth;
            var seriesColor = colors[i]

            $.each(seriesObject, function(name, value) {
                seriesName = name;
                if ($.isArray(value)) {
                    seriesData = value;
                } else {
                    seriesData = value.data;
                    seriesColor = value.color;
                }

                if (seriesType == 'line') {
                    seriesLineWidth = 3;
                } else seriesLineWidth = 4;
            });

            seriesAttributes = {name: seriesName,
                                data: seriesData,
                                color: seriesColor,
                                lineWidth: seriesLineWidth}
            chartSeries.push(seriesAttributes);
        });

        // setup HighCharts chart
        this.trafficChart = new Highcharts.Chart({
            chart: {
                renderTo: 'dashboard-stats-chart',
                defaultSeriesType: seriesType,
                marginTop: 0,
                marginBottom: 55,
                height: 185

            },
            plotOptions: {
                series: {
                    pointStart: data.pointStart,
                    pointInterval: data.pointInterval
                }
            },
            legend: {
                verticalAlign: "bottom",
                y: -7,
                enabled: (chartSeries.length > 1)
            },
            yAxis: {
                labels: {
                    formatter: function() {
                        if(activeMetric == 'rev' || activeMetric == 'cpm') {
                            return '$' + Highcharts.numberFormat(this.value, 0);
                        } else if(activeMetric == 'ctr') {
                            return Highcharts.numberFormat(this.value, 0) + '%';
                        } else {
                            if (this.value >= 1000000000) {
                                return Highcharts.numberFormat(this.value / 1000000000, 0) + "B";
                            } else if (this.value >= 1000000) {
                                return Highcharts.numberFormat(this.value / 1000000, 0) + "M";
                            } else if (this.value >= 1000) {
                                return Highcharts.numberFormat(this.value / 1000, 0) + "K";
                            } else if (this.value > 0) {
                                return Highcharts.numberFormat(this.value, 0);
                            } else {
                                return "0";
                            }
                        }
                        return "0";
                    }
                }
            },
            tooltip: {
                formatter: function() {
                    var text = '', value = '', total = '';
                    metric_translation = {att: 'attempts',
                                          clk: 'clicks',
                                          conv: 'conversions',
                                          imp: 'impressions',
                                          req: 'requests',
                                          cpm: 'CPM',
                                          rev: 'revenue',
                                          conv_rate: 'conversion rate',
                                          ctr: 'click through rate',
                                          fill_rate: 'fill rate', 
                                          usr: 'user count'};

                    // If the metric isn't in the dict use the unformatted name
                    var metric_name = metric_translation[activeMetric];
                    metric_name = metric_name ? metric_name : activeMetric;

                    if(activeMetric == 'rev' || activeMetric == 'cpm') {
                        value = '$' + Highcharts.numberFormat(this.y, 2);
                        if(data.total) {
                            total = '$' + Highcharts.numberFormat(this.total, 2) + ' total';
                        }
                    } else if (activeMetric == 'clk') {
                        value = Highcharts.numberFormat(this.y, 0) + ' ' + metric_name;
                        if(data.total) {
                            total = Highcharts.numberFormat(this.total, 0) + ' total ' + metric_name;
                        }
                    } else if (activeMetric == 'ctr') {
                        value = Highcharts.numberFormat(this.y*100, 2) + "% click through";
                    } else {
                        value = Highcharts.numberFormat(this.y, 0) + ' ' + metric_name;
                        if(data.total) {
                            total = Highcharts.numberFormat(this.total, 0) + ' total ' + metric_name;
                        }
                    }

                    text += '<span style="font-size: 14px;">' + Highcharts.dateFormat('%A, %B %e, %Y', this.x) + '</span><br/>';
                    text += '<span style="padding: 0; font-weight: 600; color: ' + this.series.color + '">' + this.series.name + '</span>' + ': <strong style="font-weight: 600;">' + value + '</strong><br/>';

                    if(chartSeries.length > 1) {
                        text += '<span style="font-size: 12px; color: #666;">';
                        if (this.total > 0 && total) {
                            text += '(' + Highcharts.numberFormat(this.percentage, 0) + '% of ' + total + ')';
                        } else if (total) {
                            text += '(' + total + ')';
                        }
                        text += '</span>';
                    }
                    return text;
                }
            },
            series: chartSeries
        });

        $('#dashboard-stats-chart').removeClass('chart-loading');
     };

    Chart.chartError = function() {
        $('#dashboard-stats-chart').removeClass('chart-loading').addClass('chart-error');
    };


    window.mopub = mopub;
    window.mopub.Stats = Stats;
    window.mopub.Chart = Chart;
    window.mopub.Controllers = {};


})(this.jQuery);


(function($){

    var config = window.ToastjsConfig = {
        defaultTimeOut: 5000,
        position: ["top", "right"],
        notificationStyles: {
            padding: "12px 18px",
            margin: "0 0 6px 0",
            backgroundColor: "#000",
            opacity: 0.8,
            color: "#fff",
            font: "normal 13px 'Droid Sans', sans-serif",
            borderRadius: "3px",
            boxShadow: "#999 0 0 12px",
            width: "300px"
        },
        notificationStylesHover: {
            opacity: 1,
            boxShadow: "#000 0 0 12px"
        },
        container: $("<div></div>")
    };

    $(document).ready(function() {
        config.container.css("position", "absolute");
        config.container.css("z-index", 9999);
        config.container.css(config.position[0], "12px");
        config.container.css(config.position[1], "12px");
        $("body").append(config.container);
    });

    function getNotificationElement() {
        return $("<div>").css(config.notificationStyles).hover(function() {
            $(this).css(config.notificationStylesHover);
        }, function() {
            $(this).css(config.notificationStyles);
        });
    }

    var Toast = window.Toast = {};

    Toast.notify = function(message, title, iconUrl, timeOut) {
        var notificationElement = getNotificationElement();

        timeOut = timeOut || config.defaultTimeOut;

        if (iconUrl) {
            var iconElement = $("<img/>", {
                src: iconUrl,
                css: {
                    width: 36,
                    height: 36,
                    display: "inline-block",
                    verticalAlign: "middle",
                    float: "left"
                }
            });
            notificationElement.append(iconElement);
        }

        var textElement = $("<div/>").css({
            display: 'inline-block',
            verticalAlign: 'middle',
            padding: '0 12px'
        });

        if (title) {
            var titleElement = $("<div/>");
            titleElement.append(document.createTextNode(title));
            titleElement.css("font-weight", "bold");
            textElement.append(titleElement);
        }

        if (message) {
            var messageElement = $("<div/>");
            messageElement.css("width", "230px");
            messageElement.css("float", "left");
            messageElement.html(message);
            textElement.append(messageElement);
        }

        notificationElement.delay(timeOut).fadeOut(function(){
            notificationElement.remove();
        });
        notificationElement.bind("click", function() {
            notificationElement.hide();
        });

        notificationElement.append(textElement);
        config.container.prepend(notificationElement);
    };

    Toast.info = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.warning = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.error = function(message, title) {
        Toast.notify(message, title, "/images/36x36-error.png");
    };

    Toast.success = function(message, title) {
        Toast.notify(message, title, "/images/36x36-success.png");
    };

}(window.jQuery));
