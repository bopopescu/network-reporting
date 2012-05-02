/*
 * ## initializeDateButtons
 * Loads all click handlers/visual stuff for the date buttons. Used
 * on a ton of pages, probably could be refactored by someone brave
 * enough.
 */
function initializeDateButtons () {
    $('#dashboard-dateOptions input').click(function() {
        var option = $(this).val();
        if (option == 'custom') {
            $('#dashboard-dateOptions-custom-modal').dialog({
                width: 570,
                buttons: [
                    {
                        text: 'Set dates',
                        css: { fontWeight: '600' },
                        click: function() {
                            var from_date = $('#dashboard-dateOptions-custom-from').xdatepicker("getDate");
                            var to_date = $('#dashboard-dateOptions-custom-to').xdatepicker("getDate");
                            var num_days = Math.ceil((to_date.getTime()-from_date.getTime())/(86400000)) + 1;

                            var from_day = from_date.getDate();
                            // FYI, months are indexed from 0
                            var from_month = from_date.getMonth() + 1;
                            var from_year = from_date.getFullYear();

                            $(this).dialog("close");
                            var location = document.location.href.replace(/\?.*/,'');
                            document.location.href = location
                                + '?r=' + num_days
                                + '&s=' + from_year + "-" + from_month + "-" + from_day;
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
            var location = document.location.href.replace(/\?.*/,'');
            document.location.href = location + '?r=' + option;
        }
    });


    // set up stats breakdown dateOptions
    $('#stats-breakdown-dateOptions input').click(function() {
        $('.stats-breakdown-value').hide();
        $('.stats-breakdown-value.'+$(this).val()).show();
    });

    // set up custom dateOptions modal dialog
    $('#dashboard-dateOptions-custom-from').xdatepicker({
        defaultDate: '-15d',
        maxDate: '0d',
        onSelect: function(selectedDate) {
            var other = $('#dashboard-dateOptions-custom-to');
            var instance = $(this).data("datepicker");
            var date = $.xdatepicker.parseDate(instance.settings.dateFormat
                                              || $.xdatepicker._defaults.dateFormat,
                                              selectedDate,
                                              instance.settings);
            other.xdatepicker('option', 'minDate', date);
        }
    });

    $('#dashboard-dateOptions-custom-to').xdatepicker({
        defaultDate: '-1d',
        maxDate: '0d',
        onSelect: function(selectedDate) {
            var other = $('#dashboard-dateOptions-custom-from');
            var instance = $(this).data("datepicker");
            var date = $.xdatepicker.parseDate(instance.settings.dateFormat ||
                                              $.xdatepicker._defaults.dateFormat,
                                              selectedDate,
                                              instance.settings);
            other.xdatepicker('option', 'maxDate', date);
        }
    });
}

