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
            var mapper_row = $("tr#" + this.model.get("app_identifier") + "-on-" + this.model.get("network") + "-row");
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

    window.AccountRollUpView = AccountRollUpView;
    window.DailyStatsView = DailyStatsView;
    window.AppOnNetworkView = AppOnNetworkView;
    window.RollUpView = RollUpView;

})(this.jQuery, this.Backbone);
