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
     * # CollectionGraphView
     * Renders a collection as a graph
     */

    var CollectionGraphView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },

        show_chart: function () {
            if(this.collection.isFullyLoaded()) {
                var active_chart = $('#dashboard-stats .stats-breakdown .active');
                var use_ctr = active_chart.attr('id') === 'stats-breakdown-ctr';
                mopub.Chart.setupDashboardStatsChart(use_ctr ? 'line' : 'area');
            }
        },

        render: function () {
            var this_view = this;
            if (this_view.collection.isFullyLoaded()) {

                var metrics = ['impression_count', 'revenue', 'click_count', 'ctr'];

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
                    impression_count: this_view.collection.get_chart_data('impression_count'),
                    revenue: this_view.collection.get_chart_data('revenue'),
                    click_count: this_view.collection.get_chart_data('click_count'),
                    ctr: this_view.collection.get_chart_data('ctr')
                };
                this_view.show_chart();
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
            try {
                this.template = _.template($('#app-template').html());
            } catch (e) {
                // the template wasn't specified. this is ok if you
                // intend to renderInline
            }
        },

        renderInline: function () {
            /*jslint maxlen: 200 */
            var app_row = $('tr.app-row#app-' + this.model.id, this.el);
            $('.revenue', app_row).text(mopub.Utils.formatCurrency(this.model.get('revenue')));
            $('.impressions', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('impressions')));
            $('.ecpm', app_row).text(mopub.Utils.formatCurrency(this.model.get('ecpm')));
            $('.clicks', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('clicks')));
            $('.ctr', app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('ctr')));
            $('.fill_rate', app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('fill_rate')));
            $('.requests', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.attempts', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.conversions', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('conversions')));
            $('.conv_rate', app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('conversion_rate')));
            /*jslint maxlen: 110 */

            $(".loading-img", app_row).hide();

            return this;
        },
        render: function () {
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
            $('.revenue', adunit_row).text(mopub.Utils.formatCurrency(this.model.get('revenue')));
            $('.ecpm', adunit_row).text(mopub.Utils.formatCurrency(this.model.get('ecpm')));
            $('.impressions', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('impressions')));
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

            $('.fill_rate', adunit_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('fill_rate')));
            $('.ctr', adunit_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('ctr')));
            $('.clicks', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('clicks')));
            $('.requests', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.attempts', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.conversions', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('conversions')));
            $('.conv_rate', adunit_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('conversion_rate')));
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

    var CampaignView = Backbone.View.extend({
        initialize: function () {
            try {
                this.template = _.template($('#adunit-template').html());
            } catch (e) {
                // you load the template partial in the page. ok if
                // you intend to renderInline.
            }
        },

        renderInline: function () {
            var current_model = this.model;
            var order_row = $('tr.order-row#order-' + this.model.get('key'), this.el);

            var display_fields = ['requests', 
                                  'impressions', 
                                  'fill_rate', 
                                  'clicks', 
                                  'ctr'];
            _.each(display_fields, function(field){
                $("." + field, order_row).text(current_model.get_formatted_stat(field));
            });

            $(".loading-img", order_row).hide();
        }
        
    });

    window.AdUnitView = AdUnitView;
    window.AppView = AppView;
    window.CampaignView = CampaignView;
    window.CollectionGraphView = CollectionGraphView;

}(this.jQuery, this.Backbone, this._));
