(function($, Backbone) {

    /*
     * ## RollUpView
     *
     * See templates/partials/app_on_network.html to see how this is rendered in HTML.
     * This renders an app on a network as a table row.
     */
    var RollUpView = Backbone.View.extend({

        initialize: function () {
            this.model.bind('change', this.render, this);
        },

        render: function () {
            var app_row = $("tr#" + this.model.id + "-row");
            $(".revenue", app_row).text(mopub.Utils.formatCurrency(this.model.get("revenue")));
            $(".attempts", app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("attempts")));
            $(".impressions", app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $(".cpm", app_row).text(mopub.Utils.formatCurrency(this.model.get("cpm")));
            $(".fill-rate", app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get("fill_rate")));
            $(".clicks", app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("clicks")));
            $(".cpc", app_row).text(mopub.Utils.formatCurrency(this.model.get("cpc")));
            $(".ctr", app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get("ctr")));

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
            this.el = this.options.el;
            this.collection.bind('change', this.render, this);
        },

        render: function () {
            var models = this.collection.models;
            var attributes = models[models.length - 1].attributes;

            console.log(attributes);
            if (attributes.mapper_key != 'undefined') {
                context_dict = {
                    name: attributes.app_name + '  ',
                    key: attributes.mapper_key,
                    url: '/ad_network_reports/app_view/' + attributes.mapper_key,
                    revenue: mopub.Utils.formatCurrency(attributes.revenue),
                    attempts: mopub.Utils.formatNumberWithCommas(attributes.attempts),
                    impressions: mopub.Utils.formatNumberWithCommas(attributes.impressions),
                    cpm: mopub.Utils.formatCurrency(attributes.cpm),
                    fill_rate: mopub.Utils.formatNumberAsPercentage(attributes.fill_rate),
                    clicks: mopub.Utils.formatNumberWithCommas(attributes.clicks),
                    cpc: mopub.Utils.formatCurrency(attributes.cpc),
                    ctr: mopub.Utils.formatNumberAsPercentage(attributes.ctr),
                }
                network_html = _.template($('#app-on-network-row-template').html(), context_dict);

                $('#app-on-' + attributes.network).append(network_html);

                // It will always insert in alphabetical order since we pull stats
                // from the networks in alphabetical order
                context_dict['name'] = attributes.network_name + '  '
                app_html = _.template($('#app-on-network-row-template').html(), context_dict);
                $('#' + attributes.app_key + '-on-networks').append(app_html);

                $('.details-row').mouseover(function () {
                    var key = $(this).attr('id');
                    $('.details-' + key).removeClass('hidden');
                });

                $('.details-row').mouseout(function () {
                    var key = $(this).attr('id');
                    $('.details-' + key).addClass('hidden');
                });
            }

            return this;
        },
    });

    window.AppOnNetworkView = AppOnNetworkView;
    window.RollUpView = RollUpView;

})(this.jQuery, this.Backbone);
