(function($, Backbone) {
    /*
     * collection: AdGroups
     * el: element that will hold the content
     * title: title that will be an h2 at the top of the content
     * type: 'network', 'gtee', 'promo', or 'backfill_promo' -- affects which fields are shown
     * tables: mapping of 
     */
    AdGroupsView = Backbone.View.extend({
        initialize: function() {
            this.collection.bind('change', this.render, this);
        },
        filtered_collection: function() {
            // TODO: uses elements not in this view
            var status = $("#campaigns-filterOptions").find(':checked').val();
            var app = $('#campaigns-appFilterOptions').val();
            return new AdGroups(this.collection.reject(function(adgroup) {
                return (status && status != adgroup.get('status')) ||
                       (app && adgroup.get('apps').indexOf(app) == -1);
            }));
        },
        render: function() {
            var adgroups = this.filtered_collection();

            // TODO: uses elements not in this view, with multiple views there are conflicts
            $("#campaigns-filterOptions").buttonset({"disabled": !adgroups.isFullyLoaded()});

            var html;
            if(adgroups.size() === 0) {
                html = "<h2>No " + this.options.title + "</h2>";
            }
            else {
                html = _.template($('#adgroups-rollup-template').html(), {
                    adgroups: adgroups,
                    title: this.options.title,
                    type: this.options.type
                });
                if(this.options.tables) {
                    var type = this.options.type;
                    _.each(this.options.tables, function(filter, title) {
                        var filtered_adgroups = new AdGroups(adgroups.filter(filter));
                        if(filtered_adgroups.length) {
                            html += _.template($('#adgroups-table-template').html(), {
                                adgroups: filtered_adgroups,
                                title: title,
                                type: type
                            });
                        }
                    });
                }
                else {
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

    CollectionGraphView = Backbone.View.extend({
        initialize: function() {
            this.collection.bind('change', this.render, this);
        },
        show_chart: function() {
            if(this.collection.isFullyLoaded()) {
                mopub.Chart.setupDashboardStatsChart( ($('#dashboard-stats .stats-breakdown .active').attr('id') == 'stats-breakdown-ctr') ? 'line' : 'area');
            }
        },
        render: function() {
            if(this.collection.isFullyLoaded()) {
                // Breakdown
                $("#stats-breakdown-impression_count .all .inner").html(this.collection.get_formatted_stat('impression_count'));
                $("#stats-breakdown-revenue .all .inner").html(this.collection.get_formatted_stat('revenue'));
                $("#stats-breakdown-click_count .all .inner").html(this.collection.get_formatted_stat('click_count'));
                $("#stats-breakdown-ctr .all .inner").html(this.collection.get_formatted_stat('ctr'));
                if(this.options.yesterday != null && this.options.today != null) {
                    // yesterday
                    $("#stats-breakdown-impression_count .yesterday .inner").html(this.collection.get_formatted_stat_for_day('impression_count', this.options.yesterday));
                    $("#stats-breakdown-revenue .yesterday .inner").html(this.collection.get_formatted_stat_for_day('revenue', this.options.yesterday));
                    $("#stats-breakdown-click_count .yesterday .inner").html(this.collection.get_formatted_stat_for_day('click_count', this.options.yesterday));
                    $("#stats-breakdown-ctr .yesterday .inner").html(this.collection.get_formatted_stat_for_day('ctr', this.options.yesterday));
                    // today
                    $("#stats-breakdown-impression_count .today .inner").html(this.collection.get_formatted_stat_for_day('impression_count', this.options.today));
                    $("#stats-breakdown-revenue .today .inner").html(this.collection.get_formatted_stat_for_day('revenue', this.options.today));
                    $("#stats-breakdown-click_count .today .inner").html(this.collection.get_formatted_stat_for_day('click_count', this.options.today));
                    $("#stats-breakdown-ctr .today .inner").html(this.collection.get_formatted_stat_for_day('ctr', this.options.today));
                }
                // Chart
                mopub.dashboardStatsChartData = {
                    pointStart: this.options.start_date,
                    pointInterval: 86400000,
                    impression_count: this.collection.get_chart_data('impression_count'),
                    revenue: this.collection.get_chart_data('revenue'),
                    click_count: this.collection.get_chart_data('click_count'),
                    ctr: this.collection.get_chart_data('ctr')
                };
                this.show_chart();
            }
        }
    })

    /*
     * ## AppView
     *
     * See templates/partials/app.html to see how this is rendered in HTML.
     * This renders an app as a table row. It also adds the call to load
     * adunits over ajax and put them in the table.
     */
    var AppView = Backbone.View.extend({

        initialize: function () {
            this.template = _.template($('#app-template').html());
        },

        renderInline: function () {
            var app_row = $("tr.app-row#app-" + this.model.id, this.el);
            $(".revenue", app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("revenue")));
            $(".impressions", app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $(".ecpm", app_row).text(this.model.get("ecpm"));
            $(".clicks", app_row).text(this.model.get("clicks"));
            $(".ctr", app_row).text(this.model.get("ctr"));
            $(".fill_rate", app_row).text(this.model.get("fill_rate"));
            $(".requests", app_row).text(this.model.get("requests"));

            return this;
        },
        render: function () {
            var renderedContent = $(this.template(this.model.toJSON()));

            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            $('a.adunits', renderedContent).click(showAdUnits);
            $('tbody', this.el).append(renderedContent);
            return this;
        }
    });

    /*
     * ## AppView helpers
     *
     * Utility methods for AppView that control the showing/hiding
     * of adunits underneath an app row.
     */
    function showAdUnits(event){
        event.preventDefault();
        var href = $(this).attr('href').replace('#','');
        Marketplace.fetchAdunitsForApp(href);
        $(this).text('Hide AdUnits').unbind("click").click(hideAdUnits);
    }

    function hideAdUnits(event){
        event.preventDefault();
        var href = $(this).attr('href').replace('#','');
        $.each($(".for-app-" + href), function (iter, item) {
            $(item).remove();
        });
        $("#app-" + href + " a.view_targeting").removeClass("hidden");
        $(this).text('Show Adunits').unbind("click").click(showAdUnits);
    }



    /*
     * ## AdUnitView
     *
     * See templates/partials/adunit.html to see how this is rendered in HTML
     * Renders an adunit as a row in a table. Also ads the event handler to
     * submit the price floor change over ajax when the price_floor field is changed.
     */
    var AdUnitView = Backbone.View.extend({

        initialize: function () {
            this.template = _.template($('#adunit-template').html());
        },

        /*
         * Render the AdUnit into a table row that already exists. Adds handlers
         * for changing AdUnit attributes over ajax.
         */
        renderInline: function () {
            var current_model = this.model;
            var adunit_row = $("tr.adunit-row#adunit-" + this.model.id, this.el);

            $(".revenue", adunit_row).text(this.model.get("revenue"));
            $(".ecpm", adunit_row).text(this.model.get("ecpm"));
            $(".impressions", adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $(".price_floor", adunit_row).html('<img class="loading-img hidden" src="/images/icons-custom/spinner-12.gif"></img> ' +
                                               '<input id="' +
                                               this.model.id +
                                               '" type="text" class="input-text input-text-number number" style="width:50px;margin: -3px 0;" value="' +
                                               this.model.get("price_floor") +
                                               '"> ');
            $(".targeting", adunit_row).html('<img class="loading-img hidden"  src="/images/icons-custom/spinner-12.gif"></img> ' +
                                             '<input class="targeting-box" type="checkbox">');


            $(".fill_rate", adunit_row).text(this.model.get("fill_rate"));
            $(".ctr", adunit_row).text(this.model.get("ctr"));
            $(".clicks", adunit_row).text(this.model.get("clicks"));
            $(".requests", adunit_row).text(this.model.get("requests"));

            if (this.model.get("active")) {
                $("input.targeting-box", adunit_row).attr('checked', 'checked');
            }

            // Add the event handler to submit targeting changes over ajax.
            $("input.targeting-box", adunit_row).click(function() {
                var loading_img = $(".targeting .loading-img", adunit_row);
                loading_img.show();
                current_model.set({'active': $(this).is(":checked")});
                current_model.save({}, {
                    success: function () {
                        setTimeout(function() {
                            loading_img.hide();
                        }, 2000);
                    }
                });
            });

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor .input-text', adunit_row).keyup(function() {
                var loading_img = $(".price_floor .loading-img", adunit_row);
                loading_img.show();
                current_model.set({'price_floor': $(this).val()});
                current_model.save({}, {
                    success: function () {
                        setTimeout(function() {
                            loading_img.hide();
                        }, 2000);
                    }
                });
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
                .change(function() {
                    current_model.set({'price_floor': $(this).val()});
                    // Save when they click the save button in the price floor cell
                    var save_link = $(".save", $(this).parent());
                        save_link.click(function(e) {
                            e.preventDefault();
                            save_link.addClass('disabled').text('Saving...');
                            current_model.save({}, {
                                success: function () {
                                    setTimeout(function() {
                                        save_link.removeClass('disabled').text('Saved');
                                        save_link.text("Save");
                                    }, 2000);
                                }
                            });
                        });
                });

            // Add the event handler to submit targeting changes over ajax.
            $("input.targeting-box", renderedContent).click(function() {
                var targeting = $(this).attr('name');
                var activation = $(this).is(":checked") ? "On" : "Off";
                $("label[for='"+ targeting +"']", renderedContent).text(activation);

                current_model.set({'active': $(this).is(":checked")});
                current_model.save();
            });

            // Add the right background color based on where the app is in the table
            var app_row = $('tr#app-' + this.model.get('app_id'), this.el);
            var zebra = app_row.hasClass("even") ? "even" : "odd";
            renderedContent.addClass(zebra);

            app_row.after(renderedContent);

            return this;
        }
    });

    window.AdUnitView = AdUnitView;
    window.AppView = AppView;

})(this.jQuery, this.Backbone);