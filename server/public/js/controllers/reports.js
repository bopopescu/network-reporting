(function($, _) {
    var ReportIndexController = {
        initialize: function(bootstrapping_data) {
                        var report_keys = bootstrapping_data.report_keys;

                        var submit_button;

                        /* Add a new report UI */
                        // Show new report form
                        $('#reports-addReportButton').button({icons: {primary: 'ui-icon-circle-plus'}})
                            .click(function(e){
                                e.preventDefault();
                                var report_form = $('#reports-reportAddForm');
                                if (report_form.is(':hidden')) {
                                    $('#reports-reportAddForm').slideDown('fast');
                                }
                                else {
                                    $('#reports-reportAddForm').slideUp('fast');
                                }
                            });


                        // set up form fields for the new report form
                        set_up_form('new');

                        // Create new report
                        $('#new-reportEditForm-run')
                            .button({label: 'Run',
                                icons: {secondary: 'ui-icon-circle-triangle-e' }})
                            .click(function(e) {
                                e.preventDefault();
                                submit_button = $(this);
                                $('#new-reportEditForm').submit();
                            });

                        // Cancel new report form
                        $('#new-reportEditForm-cancel').button()
                            .click(function(e) {
                                e.preventDefault();
                                $('#reports-reportAddForm').slideUp('fast');
                            });

                        // set up selects as chosen elements
                        $('.chzn-select').chosen();

                        /* Edit existing saved and scheduled reports */
                        _.each(report_keys, function(report_key) {
                            // reports use the same form as their scheduled
                            // report
                            var key = report_key[0];
                            var scheduled_key = report_key[1];

                            var row = $('#' + key + '-row')

                            // hide / show wrench edit icon
                            $(row).mouseenter(function(e) {
                                $('#' + key + '-edit-link').show();
                            })
                            $(row).mouseleave(function(e) {
                                $('#' + key + '-edit-link').hide();
                            })

                            // when wrench is clicked open an edit report form dialog
                            $('#' + key + '-edit-link')
                                .click(function(e) {
                                    e.preventDefault();
                                    var report_form = $('#' + scheduled_key + '-reportForm-container');
                                    report_form.dialog({width:750});
                                });

                            if (scheduled_key == key) {
                                // close dialog
                                $('#' + scheduled_key + '-reportEditForm-cancel')
                                    .click(function(e) {
                                        e.preventDefault();
                                        $('#' + scheduled_key + '-reportForm-container').dialog('close');
                                    });


                                // set up form fields
                                set_up_form(scheduled_key);
                            }

                        });

                        /* Delete report */
                        $('#reportStateChangeForm-delete')
                            .click(function(e) {
                                e.preventDefault();
                                $('#reportStateChangeForm').find('#action').val('delete').end().submit();
                            });


                    }
    }


    var ONE_DAY = 1000*60*60*24
    /* set up the js for a ReportForm */
    function set_up_form(prefix) {
        // based on d1's selection, modify options for d2 and d3 
        $('#id_' + prefix + '-d1').change(
                function(e) {
                    e.preventDefault();
                    d1_validate(prefix);
                    d2_validate(prefix);
                }).change();

        // based on d2's selection, modify options for d3 
        $('#id_' + prefix + '-d2').change(
                function(e) {
                    e.preventDefault();
                    d2_validate(prefix);
                });

        // set date fields based on selected interval
        $('#id_' + prefix + '-interval')
            .change(function(e) {
                if(val != 'custom') {
                    var val = $(this).val();
                    // date initialized as today
                    var date = new Date();
                    switch (val) {
                        case 'yesterday':
                            date.setTime(date.getTime() - ONE_DAY);
                            var start = date.format("m/dd/yyyy");
                            var end = start;
                            break;
                        case '7days':
                            var end = date.format("m/dd/yyyy");
                            date.setTime(date.getTime() - (7 * ONE_DAY));
                            var start= date.format("m/dd/yyyy");
                            break;
                        case 'lmonth':
                            var this_mo = date.getMonth();
                            while (date.getMonth() == this_mo) {
                                date.setTime(date.getTime() - ONE_DAY);
                            }
                            var end = date.format("m/dd/yyyy");
                            date.setDate(1);
                            var start = date.format("m/dd/yyyy");
                            break;
                    }
                    $('#id_' + prefix + '-start').val(start);
                    $('#id_' + prefix + '-end').val(end);
                }
            }).change();

        // change interval to custom if user enters anything in a date field
        $('.date')
            .change(function(e) {
                $('#id_' + prefix + '-interval').val('custom');
                $('#id_' + prefix + '-interval').trigger("liszt:updated");
            });

        // change help text for scheduled interval
        $('#id_' + prefix + '-sched_interval')
            .change(function(e) {
                // hide all shceduled helps
                $('#id_' + prefix + '-schedule-help').hide();
                // show help for value
                $('#id_' + prefix + '-schedule-help-' + $(this).val()).show();
            }).change();

        // Validate report forms
        var validator = $('#' + prefix + '-reportEditForm').validate({
            errorPlacement: function(error, element) {
                                element.parents('div').not(':hidden').first().append(error);
                            },
            submitHandler: function(form) {
                               $(form).ajaxSubmit({
                                   data: {ajax: true},
                                   dataType: 'json',
                                   success: function(jsonData, statusText, xhr, $form) {
                                       window.location = jsonData.redirect;
                                       if(jsonData.success) {
                                           $('#' + prefix + '-reportEditForm.button').button({
                                               disabled: true
                                           });
                                           submit_button.button({
                                               label: 'Success...'
                                           });
                                       } else {
                                           console.log(jsonData.errors);
                                           validator.showErrors(jsonData.errors);
                                           $('#' + prefix + '-reportEditForm.button').button({
                                               disabled: false
                                           });
                                           submit_button.button({
                                               label: 'Try Again'
                                           });
                                       }
                                   },
                                   error: function(jqXHR, textStatus, errorThrown) {
                                       $('#' + prefix + '-reportEditForm.button').button({
                                           disabled: false
                                           });
                                       submit_button.button({
                                           label: 'Try Again'
                                           });
                                       },
                                   beforeSubmit: function(arr, $form, options) {
                                       $('#' + prefix + '-reportEditForm.button').button({
                                           disabled: true
                                           });
                                       submit_button.button({
                                           label: 'Submitting...'
                                           });
                                       }
                                });
                           }
        });

        // Submit form
        $('#' + prefix + '-reportEditForm-save')
            .click(function(e) {
                e.preventDefault();
                submit_button = $(this);
                $('#id_' + prefix + '-saved').attr('checked', true);
                $('#' + prefix + '-reportEditForm').submit();
            });
    }

    /* Based on d1's selection change what options are shown for d2 and d3 */
    function d1_validate(prefix) {
        var d1_sel = $('#id_' + prefix + '-d1');
        var d2_sel = $('#id_' + prefix + '-d2');
        var d3_sel = $('#id_' + prefix + '-d3');

        //start with everything
        reset_dimensions(d2_sel);
        reset_dimensions(d3_sel);

        if(d1_sel.val() == '') {
            d2_sel.children().first().select();
            d3_sel.children().first().select();
            $('#' + prefix + '-d2-show').hide();
            $('#' + prefix + '-d3-show').hide();
        } else {
            check_and_remove(d1_sel.val(), d2_sel, d3_sel);
            $('#' + prefix + '-d2-show').show();
        }

        // update chosen
        d2_sel.trigger("liszt:updated");
        d3_sel.trigger("liszt:updated");
    }


    /* Based on d2's selection change what options are shown for d3 */
    function d2_validate(prefix) {
        var d2_sel = $('#id_' + prefix + '-d2');
        var d3_sel = $('#id_' + prefix + '-d3');

        if(d2_sel.val() == '') {
            d2_sel.children().first().select();
            d3_sel.children().first().select();
            $('#' + prefix + '-d3-show').hide();
        } else {
            $('#' + prefix + '-d3-show').show();
            check_and_remove(d2_sel.val(), d3_sel);
            $('#' + prefix + '-d3-show').show();
        }

        // update chosen
        d3_sel.trigger("liszt:updated");
    }

    DIMENSIONS = [['','------------'],
               ['app', 'App'],
               ['adunit', 'Ad Unit'],
               ['priority', 'Priority'],
               ['campaign', 'Campaign'],
               ['creative', 'Creative'],
               ['month', 'Month'],
               ['week', 'Week'],
               ['day', 'Day'],
               ['hour', 'Hour'],
               ['country', 'Country'],
               ['marketing', 'Device'],
               ['os', 'OS'],
               ['os_ver', 'OS Version']]

    /* Reset dimension selector back to initial options */
    function reset_dimensions(selector) {
        // clear all options
        selector.html('');

        // rebuild options
        _.each(DIMENSIONS, function(dims) {
            dim = dims[0];
            text = dims[1];
            selector.append('<option value="' + dim + '">' + text + '</option>')
        });

        // update chosen
        selector.trigger("liszt:updated");
    }

    CONNECTED_DIMENSIONS = {'adunit': ['app'],
                            'campaign': ['priority'],
                            'creative': ['campaign', 'priority'],
                            'week': ['month'],
                            'day': ['week', 'month'],
                            'hour': ['day', 'week', 'month'],
                            'os_ver': ['os']}

    /* Check if text is selected in selects if it is, it resets the select.
     * Remove the option from the select. Remove connected options from the select.
     *
     * Take text and optional number of select objects */
    function check_and_remove(text) {
        // The selection of certain dims filters the potential set of sub dims by more
        // than just itself in instances described by CONNECTED_DIMENSIONS
        var connected_dims = [];
        if(CONNECTED_DIMENSIONS[text] !== undefined) {
            connected_dims = CONNECTED_DIMENSIONS[text];
        }

        _.each(_.toArray(arguments).slice(1), function(selector) {
            if (selector.val() == text) {
                selector.children().first.select();
            }
            selector.children('option[value="' + text + '"]').remove();

            _.each(connected_dims, function(dim) {
                selector.children('option[value="' + dim + '"]').remove();
            });
        });
    }

    window.ReportIndexController = ReportIndexController;

})(window.jQuery, window._);
