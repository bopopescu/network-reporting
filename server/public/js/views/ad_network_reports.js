(function($, Backbone) {

    /*
     * ## AccountRollUpView
     *
     */
    var AccountRollUpView = Backbone.View.extend({

        initialize: function () {
            this.model.bind('change', this.render, this);
        },

        render: function () {
            var stats_div = "#dashboard-stats .stats-breakdown";
            var inner = ".stats-breakdown-value .inner";
            $("#stats-breakdown-revenue " + inner, stats_div).text(mopub.Utils.formatCurrency(this.model.get("revenue")));
            $("#stats-breakdown-impressions " + inner, stats_div).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $("#stats-breakdown-clicks " + inner, stats_div).html('<span class="muted unbold">(' + mopub.Utils.formatNumberWithCommas(this.model.get("clicks")) + ')</span> ' + mopub.Utils.formatNumberAsPercentage(this.model.get("ctr")));

            return this;
        },
    });

    /*
     * ## DailyStatsView
     *
     * View for rendering the chart out of the daily stats.
     */
    var DailyStatsView = Backbone.View.extend({

        initialize: function () {
            this.collection.bind('reset', this.render, this);
        },

        render: function () {
            models = this.collection.models;
            var daily_stats = models.map(function(model) {
                  return model.attributes;
            });
            populateGraphWithStats(daily_stats);

            return this;
        },
    });

    /*
     * ## RollUpView
     *
     */
    var RollUpView = Backbone.View.extend({

        initialize: function () {
            this.model.bind('change', this.render, this);
        },

        render: function () {
            if(this.model.get("type") == 'network' && this.model.get("sync_date")) {
                $("#" + this.model.id + "-row .network-status span:first").append(this.model.get("sync_date"));
            }

            var mapper_row = $("tr#" + this.model.id + "-row");
            $(".revenue", mapper_row).text(mopub.Utils.formatCurrency(this.model.get("revenue")));
            $(".attempts", mapper_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("attempts")));
            $(".impressions", mapper_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $(".cpm", mapper_row).text(mopub.Utils.formatCurrency(this.model.get("cpm")));
            $(".fill-rate", mapper_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get("fill_rate")));
            $(".clicks", mapper_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("clicks")));
            $(".cpc", mapper_row).text(mopub.Utils.formatCurrency(this.model.get("cpc")));
            $(".ctr", mapper_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get("ctr")));

            return this;
        },
    });

    /*
     * ## AppOnNetworkView
     *
     * See templates/partials/app_on_network.html to see how this is rendered in HTML.
     * This renders an app on a network as a table row.
     */
    var AppOnNetworkView = Backbone.View.extend({

        initialize: function () {
            this.model.bind('change', this.render, this);
        },

        render: function () {
            console.log('i was called');
            var context_dict = {
                name: this.model.get('app_name') + '  ',
                network: this.model.get('network_name'),
                key: this.model.get('mapper_key'),
                url: '/ad_network_reports/app_view/' + this.model.get('mapper_key'),
                revenue: mopub.Utils.formatCurrency(this.model.get('revenue')),
                attempts: mopub.Utils.formatNumberWithCommas(this.model.get('attempts')),
                impressions: mopub.Utils.formatNumberWithCommas(this.model.get('impressions')),
                cpm: mopub.Utils.formatCurrency(this.model.get('cpm')),
                fill_rate: mopub.Utils.formatNumberAsPercentage(this.model.get('fill_rate')),
                clicks: mopub.Utils.formatNumberWithCommas(this.model.get('clicks')),
                cpc: mopub.Utils.formatCurrency(this.model.get('cpc')),
                ctr: mopub.Utils.formatNumberAsPercentage(this.model.get('ctr'))
            };
            var network_html = _.template($('#app-on-network-row-template').html(), context_dict);

            $('#app-on-' + this.model.get('network')).append(network_html);

            // It will always insert in alphabetical order since we pull stats
            // from the networks in alphabetical order
            context_dict['name'] = this.model.get('network_name') + '  ';
            var app_html = _.template($('#app-on-network-row-template').html(), context_dict);
            $('#' + this.model.get('app_key') + '-on-networks').append(app_html);

            $('.details-row').mouseover(function () {
                var key = $(this).attr('id');
                $('.details-' + key).removeClass('hidden');
            });

            $('.details-row').mouseout(function () {
                var key = $(this).attr('id');
                $('.details-' + key).addClass('hidden');
            });

            return this;
        }
    });

    window.AccountRollUpView = AccountRollUpView;
    window.DailyStatsView = DailyStatsView;
    window.AppOnNetworkView = AppOnNetworkView;
    window.RollUpView = RollUpView;

})(this.jQuery, this.Backbone);
