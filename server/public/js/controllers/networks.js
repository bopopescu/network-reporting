$(function() {
    // TODO: document
    /*
     *   adgroups_data
     *   graph_start_date
     *   today
     *   yesterday
     *   ajax_query_string
     */

    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    var NetworksController = {

        initialize: function(bootstrapping_data) {
            var adgroups_data = bootstrapping_data.adgroups_data,
                graph_start_date = bootstrapping_data.graph_start_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            var adgroups = new AdGroups(adgroups_data);

            var graph_view = new CollectionGraphView({
                collection: adgroups,
                start_date: graph_start_date,
                today: today,
                yesterday: yesterday
            });
            graph_view.render();

            var adgroups_view = new AdGroupsView({
                collection: adgroups,
                el: '#adgroups',
                title: 'Ad Networks',
                type: 'network'
            });
            adgroups_view.render();

            adgroups.each(function(adgroup) {
                adgroup.fetch({
                    data: ajax_query_string,
                    error: function () {
                        adgroup.fetch({
                            error: toast_error
                        });
                    }
                });
            });

            // TODO: move to views
            // date picker
            // set up dateOptions
            $('#dashboard-dateOptions input').click(function() {
                var option = $(this).val();
                    var hash = document.location.hash;
                if(option == 'custom') {
                    $('#dashboard-dateOptions-custom-modal').dialog({
                        width: 570,
                        buttons: [
                            {
                                text: 'Set dates',
                                css: { fontWeight: '600' },
                                click: function() {
                                    var from_date=$('#dashboard-dateOptions-custom-from').datepicker("getDate");
                                    var to_date=$('#dashboard-dateOptions-custom-to').datepicker("getDate");
                                    var num_days=Math.round((to_date.getTime()-from_date.getTime())/(86400000));

                                    var from_day=from_date.getDate();
                                    var from_month=from_date.getMonth()+1;
                                    var from_year=from_date.getFullYear();

                                    $(this).dialog("close");
                                    var location = document.location.href.replace(hash, '').replace(/\?.*/,'');
                                    document.location.href = location+'?r='+num_days+'&s='+from_year+"-"+from_month+"-"+from_day + hash;
                                }
                            },
                            {
                                text: 'Cancel',
                                click: function() {
                                    $(this).dialog("close");
                                }
                            }
                        ]
                    });
                } else {
                    // Tell server about selected option to get new data
                    var location = document.location.href.replace(hash,'').replace(/\?.*/,'');
                    document.location.href = location+'?r=' + option + hash;
                }
            });


            // set up custom dateOptions modal dialog
            $('#dashboard-dateOptions-custom-from').datepicker({
                defaultDate: '-15d',
                maxDate: '0d',
                    onSelect: function(selectedDate) {
                        var other = $('#dashboard-dateOptions-custom-to');
                        var instance = $(this).data("datepicker");
                        var date = $.datepicker.parseDate(instance.settings.dateFormat ||
                                                          $.datepicker._defaults.dateFormat,
                                                          selectedDate,
                                                          instance.settings);
                        other.datepicker('option', 'minDate', date);
                    }
        });

            $('#dashboard-dateOptions-custom-to').datepicker({
                defaultDate: '-1d',
                maxDate: '0d',
                onSelect: function(selectedDate) {
                    var other = $('#dashboard-dateOptions-custom-from');
                    var instance = $(this).data("datepicker");
                    var date = $.datepicker.parseDate(instance.settings.dateFormat ||
                                                      $.datepicker._defaults.dateFormat,
                                                      selectedDate,
                                                      instance.settings);
                    other.datepicker('option', 'maxDate', date);
                }
            });

            var self = this;
            // stats breakdown
            $('.stats-breakdown tr').click(function(e) {
                var row = $(this);
                if(!row.hasClass('active')) {
                    row.siblings().removeClass('active');
                    row.addClass('active');
                    $('#dashboard-stats-chart').fadeOut(100, function() {
                        graph_view.show_chart();
                        $(this).show();
                    });
                }
            });

            $('#stats-breakdown-dateOptions input').click(function() {
                $('.stats-breakdown-value').hide();
                $('.stats-breakdown-value.'+$(this).val()).show();
            });

            $('.stats-breakdown-value').hide();
            $('.stats-breakdown-value.all').show();

            // Ad Campaign button
            $("#add_campaign_button").button({
                icons : { primary : 'ui-icon-circle-plus'}
            });


            // AdGroups form
            var actions = ['pause', 'resume', 'activate', 'archive', 'delete'];
            $.each(actions, function(iter, action) {
                $('#campaignForm-' + action).click(function(e) {
                    e.preventDefault();
                    $('#campaignForm')
                        .find("#action")
                        .attr("value", action)
                        .end()
                        .submit();
                });
            });
        }
    };

    window.NetworksController = NetworksController;
});
