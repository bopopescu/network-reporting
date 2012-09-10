(function() {
    
    var submit_button;
    
    var ReportIndexController = {
        initialize: function(bootstrapping_data) {
            var report_keys = bootstrapping_data.report_keys;
            
            
            /* Add a new report UI */
            // Show new report form
            $('#reports-addReportButton')
                .click(function(e){
                    e.preventDefault();
                    var report_form = $('#reports-reportAddForm');
                    if (report_form.is(':hidden')) {
                        $('#reports-reportAddForm').slideDown('fast');
                    } else {
                        $('#reports-reportAddForm').slideUp('fast');
                    }
                });
            
            
            // set up form fields for the new report form
            set_up_form('new');
            
            // initialize the interval
            $('#id_new-interval').change();
            
            // Hide / Show run button based on sched interval
            // selection
            $('#id_new-sched_interval').change(function(e) {
                if($(this).val() == 'none') {
                    // Show run button
                    $('#new-reportEditForm-run').show();
                } else {
                    // Hide run button
                    $('#new-reportEditForm-run').hide();
                }
            }).change();
            
            // Create new report
            $('#new-reportEditForm-run').click(function(e) {
                e.preventDefault();
                submit_button = $(this);
                $('#new-reportEditForm').submit();
            });
            
            // Cancel new report form
            $('#new-reportEditForm-cancel').click(function(e) {
                e.preventDefault();
                $('#reports-reportAddForm').slideUp('fast');
            });
            
            // set up selects as chosen elements
            $('.chzn-select').chosen();
            
            /* Edit existing saved and scheduled reports */
            _.each(report_keys, function(key) {
                
                var row = $('#' + key + '-row');
                
                // populate report status
                $.ajax({
                    url: 'status/' + key,
                    success: function(data) {
                        var report_status = data['status'];
                        
                        if (report_status === "Completed") {
                            $('#' + key + '-status').html('<a href=\'export/' + key + '/\' >Export</a>');
                        } else {
                            $('#' + key + '-status').html(report_status);
                        }
                    }
                });
                
                // hide / show wrench edit icon
                $(row).mouseenter(function(e) {
                    $('#' + key + '-edit-link').show();
                });

                $(row).mouseleave(function(e) {
                    $('#' + key + '-edit-link').hide();
                });
                
                // when wrench is clicked open an edit report form dialog
                $('#' + key + '-edit-link')
                    .click(function(e) {
                        e.preventDefault();
                        var report_form = $('#' + key + '-reportForm-container');
                        report_form.dialog({width:750});
                    });
                
                // close dialog
                $('#' + key + '-reportEditForm-cancel')
                    .click(function(e) {
                        e.preventDefault();
                        $('#' + key + '-reportForm-container').dialog('close');
                    });                
                
                // set up form fields
                set_up_form(key);                
            });
                
            /* Delete report */
            $('#reportStateChangeForm-delete').click(function(e) {
                e.preventDefault();
                $('#reportStateChangeForm').find('#action')
                    .val('delete')
                    .end()
                    .submit();
            });            
        }
    };
    
    
    var ONE_DAY = 1000*60*60*24;

    /* set up the js for a ReportForm */
    function set_up_form(prefix) {
        // based on d1's selection, modify options for d2 and d3 
        $('#id_' + prefix + '-d1').change(
            function(e) {
                e.preventDefault();
                d1_validate(prefix, true, true);
                d2_validate(prefix);
            });
        
        // based on d2's selection, modify options for d3 
        $('#id_' + prefix + '-d2').change(
            function(e) {
                e.preventDefault();
                d1_validate(prefix, false, true);
                d2_validate(prefix);
            });
        
        // setup initial state for d2 and d3
        d1_validate(prefix, false, false);
        d2_validate(prefix);
        
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
            });
        
        // change interval to custom if user enters anything in a date field
        $('.date').change(function(e) {
            $('#id_' + prefix + '-interval').val('custom');
            $('#id_' + prefix + '-interval').trigger("liszt:updated");
        });
        
        // change help text for scheduled interval
        $('#id_' + prefix + '-sched_interval')
            .change(function(e) {
                // hide all shceduled helps
                _.each(['daily', 'weekly', 'monthly', 'quarterly'], function(interval) {
                    $('#' + prefix + '-schedule-help-' + interval).hide();
                });
                // show help for value
                $('#' + prefix + '-schedule-help-' + $(this).val()).show();
            }).change();

        var save_btn = $('#' + prefix + '-reportEditForm-run, #' + prefix + '-reportEditForm-save');
        var spinner = $("#submit-spinner");
        var help_text = $("#form-help-text");
        // Validate report forms
        var validator = $('#' + prefix + '-reportEditForm').validate({
            errorPlacement: function(error, element) {
                // HACK: The reports form is pretty screwed up and
                // doesn't handle multi-field validation very well.
                // Because of this, all validations for both
                // start_date and end_date will only highlight
                // start_date.  So we handle this by highlighting
                // neither fields when either field has an issue, and
                // just relying on the messaging. This can probably be
                // reverted in the future if we change how the form
                // works.
                if ($(element).attr('id') !== 'id_new-start') {
                    element.parents('dd').not(':hidden').first().append(error);
                });                
            },
            submitHandler: function(form) {
                $(form).ajaxSubmit({
                    data: {ajax: true},
                    dataType: 'json',
                    success: function(jsonData, statusText, xhr, $form) {
                        if(jsonData.success) {
                            window.location = jsonData.redirect;
                            spinner.addClass('hidden');
                            help_text.text("Success");
                            save_btn.attr('disabled', 'disabled');
                        } else {
                            console.log(jsonData.errors);
                            validator.showErrors(jsonData.errors);
                            spinner.addClass('hidden');
                            help_text.text("Try Again");
                            save_btn.removeAttr('disabled');
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        spinner.addClass('hidden');
                        help_text.text("Try Again");
                        save_btn.removeAttr('disabled');
                    },
                    beforeSubmit: function(arr, $form, options) {
                        spinner.removeClass('hidden');
                        help_text.text("Submitting");
                        save_btn.attr('disabled', 'disabled');
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
    function d1_validate(prefix, reset_d2, reset_d3) {
        var d1_sel = $('#id_' + prefix + '-d1');
        var d2_sel = $('#id_' + prefix + '-d2');
        var d3_sel = $('#id_' + prefix + '-d3');
        
        //start with everything
        if(reset_d2) {
            reset_dimensions(d2_sel);
        }
        if(reset_d3) {
            reset_dimensions(d3_sel);
            $('#' + prefix + '-d3-show').hide();
        }
        
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
    
    var DIMENSIONS = [
        ['','------------'],
        ['app', 'App'],
        ['adunit', 'Ad Unit'],
        ['priority', 'Priority'],
        ['campaign', 'Order'],
        ['adgroup', 'Line Item'],
        ['creative', 'Creative'],
        ['month', 'Month'],
        ['week', 'Week'],
        ['day', 'Day'],
        ['hour', 'Hour'],
        ['country', 'Country'],
        ['marketing', 'Device'],
        ['os', 'OS'],
        ['os_ver', 'OS Version']
    ];
    
    /* Reset dimension selector back to initial options */
    function reset_dimensions(selector) {
        // clear all options
        selector.html('');
        
        // rebuild options
        _.each(DIMENSIONS, function(dims) {
            var dim = dims[0];
            var text = dims[1];
            selector.append('<option value="' + dim + '">' + text + '</option>');
        });
        
        // update chosen
        selector.trigger("liszt:updated");
    }
    
    var CONNECTED_DIMENSIONS = {
        'adunit': ['app'],
        'campaign': ['priority'],
        'creative': ['campaign', 'priority'],
        'week': ['month'],
        'day': ['week', 'month'],
        'hour': ['day', 'week', 'month'],
        'os_ver': ['os']
    };
    
    /* Check if text is selected in selects if it is, it resets the select.
     * Remove the option from the select. Remove connected options from the select.
     *
     * Take text and optional number of select objects */
    function check_and_remove(text) {
        // The selection of certain dims filters the potential set of sub dims by more
        // than just itself in instances described by CONNECTED_DIMENSIONS
        var connected_dims = [];
        if(typeof CONNECTED_DIMENSIONS[text] !== 'undefined') {
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
    
}).call(this);
