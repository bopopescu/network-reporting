(function($, _) {


    function addPlaceholder() {
        $('.reportData-placeholder').hide();
        $('table').each(function() {
            visible = $(this).find('.reportData:visible');
            if (visible.length === 0) {
                $(this).find('.reportData-placeholder').show();
            }
        });
    }
    addPlaceholder();

    $('input[name="start"]').xdatepicker().change(function (e) {
        var dte = new Date($(this).val());
        $('input[name="end"]').xdatepicker('option', 'minDate', dte);
    });

    $('input[name="end"]').xdatepicker({maxDate: new Date()}).change(function (e) {
        var dte = new Date($(this).val());
        $('input[name="start"]').xdatepicker('option', 'maxDate', dte);
    });

    function rep_validate(form) {
        /* Check a form for selectmenu-required selectmenus
         * check for date-requireds
         * If any invalid, flag as invalid (with the pretty red colors)
         * and return False
         * if nothing invalid, return True
         */
        var success = true;
        $('#d1Error').hide();
        $('#dateError').hide();
        $('select.selectmenu-required').each(function() {
            if ($(this).val() == '') {
                $('#d1Error').show();
                success = false;
            }
        });
        $('.date-required').each(function() {
            $(this).removeClass('form-error');
            if ($(this).val() == '') {
                $(this).addClass('form-error');
                $('#dateError').show();
                success = false;
            }
        });
        return success;
    }

    function ajaxSave() {
        $.ajax({
            url:'http://' + window.location.host + '/reports/save/' + $('#reportKey').val() + '/',
        success: function() {
            $('#reports-view-toIndex').click();
        }
        });
    }

    $('#reports-view-saveAsButton').button({icons: {secondary: 'ui-icon-check'}})
        .click(function(e) {
            e.preventDefault();
            $('#saveAs').val('True');
            $('#reportName-input').val('Copy of '+ $('#reportName-input').val());
            $('.dim-selectmenu').selectmenu('disable');
            $('#interval').selectmenu('disable');
            $('#start-input').xdatepicker('disable');
            $('#end-input').xdatepicker('disable');
            $('#reportEditForm-submit').button({label: 'Save As'});
            $('#sched_interval').selectmenu('index', 0).change();
            $('#reportForm-container').dialog({width:750});
        });


    var ReportIndexController = {
        initialize: function(bootstrapping_data) {
                        var report_keys = bootstrapping_data.report_keys;


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


                        // Set up d1 selection for creating new scheduled reports
                        // based on d1's selection, modify options for d2 and d3 
                        set_up_form('new');

                        // Create new report
                        $('#new-reportEditForm-run')
                            .button({label: 'Run',
                                icons: {secondary: 'ui-icon-circle-triangle-e' }})
                            .click(function(e) {
                                e.preventDefault();
                                if (rep_validate($('#new-reportEditForm'))) {
                                    $('#new-reportEditForm').submit();
                                }
                                else {
                                    $('#formError').show();
                                }
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
                        _.each(report_keys, function(key) {
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
                                    $('#' + key + '-saveAs').val('False');
                                    $('#' + key + '-reportEditForm-save').button({label: 'Save'});
                                    var report_form = $('#' + key + '-reportForm-container');
                                    report_form.dialog({width:750});
                                });

                            // close dialog
                            $('#' + key + '-reportEditForm-cancel')
                                .click(function(e) {
                                    e.preventDefault();
                                    $('.dim-selectmenu').selectmenu('enable');
                                    $('#interval').selectmenu('enable');
                                    $('#start-input').xdatepicker('enable');
                                    $('#end-input').xdatepicker('enable');
                                    // TODO
                                    //revert_state(form_state);
                                    $('#' + key + '-reportForm-container').dialog('close');
                                });

                            // TODO
                            $(row).find('.update-button')
                                .change(function(e) {
                                    e.preventDefault();
                                    if (!obj_equals(form_state, get_form_state())) {
                                        $('#' + key + 'reportEditForm-save').button({label:'Save and Run'});
                                    }
                                    else {
                                        $('#' + key + '-reportEditForm-save').button({label:'Save'});
                                    }
                                }).change();

                            set_up_form(key);

                        });

                        /* Delete report */
                        $('#reportStateChangeForm-delete')
                            .click(function(e) {
                                e.preventDefault();
                                $('#reportStateChangeForm').find('#action').val('delete').end().submit();
                            });


                    }
    }


    function fix_date(dte) {
        if (dte < 10) {
            return '0' + dte;
        }
        return dte;
    }

    function format_date(dte) {
        return fix_date(dte.getMonth() + 1) + '/' + fix_date(dte.getDate()) + '/' + dte.getFullYear();
    }


    var update = true;
    $('#interval')
        .change(function(e) {
            update = false;
            var val = $(this).val();
            var today = new Date();
            if (val != 'custom') {
                $('#interval-toggle').val(2);
                var one_day = 1000*60*60*24
            switch (val) {
                case 'yesterday':
                    today.setTime(today.getTime() - one_day);
                    var dte = format_date(today);
                    $('#end-input').val(dte).change();
                    $('#start-input').val(dte).change();
                    break;
                case '7days':
                    var dte = format_date(today);
                    $('#end-input').val(dte).change();
                    today.setTime(today.getTime() - (7*one_day));
                    dte = format_date(today);
                    $('#start-input').val(dte).change();
                    break;
                case 'lmonth':
                    var this_mo = today.getMonth();
                    while (today.getMonth() == this_mo) {
                        today.setTime(today.getTime() - one_day);
                    }
                    var dte = format_date(today);
                    $('#end-input').val(dte).change();
                    today.setDate(1);
                    dte = format_date(today);
                    $('#start-input').val(dte).change();
                    break;
            }
            }
            else {
                return;
            }
        }).change();

    $('.date-field')
        .change(function(e) {
            var inter_val = $('#interval-toggle').val()
            if ($('#interval-toggle').val() == 0) {
                $('#interval').selectmenu('index', 3);
            }
            else {
                $('#interval-toggle').val(inter_val - 1);
            }
        });

    function revert_state(state) {
        d1_sel.selectmenu('index', state.d1);
        d1_validate($('#d1'));
        d2_sel.selectmenu('index', state.d2);
        d2_validate($('#d2'));
        d3_sel.selectmenu('index', state.d3);
        $('#end-input').val(state.end);
        $('#start-input').val(state.start);
        $('#interval').selectmenu('index', state.interv);
        $('#sched_interval').selectmenu('index', state.sched_interv);
        // Trigger those on change events what whatttt
        $('#interval').change();
        $('#sched_interval').change();
        $("#reportName-input").val(state.name);
        if (state.email) {
            $('#email-input-checkbox').attr('checked');
        }
        else {
            $('#email-input-checkbox').removeAttr('checked');
        }
    }

    function get_form_state(d1_sel, d2_sel, d3_sel) {
        return build_state( sel_state(d1_sel),
                sel_state(d2_sel),
                sel_state(d3_sel),
                sel_state($('#interval')),
                sel_state($('#sched_interval')),
                $('#end-input').val(),
                $('#start-input').val(),
                $('#reportName-input').val(),
                $('#email-input-checkbox')
                );
    }
    function build_state(d1, d2, d3, interv, sched_interv, end, start, name, email) {
        return {
            d1: d1,
            d2: d2,
            d3: d3,
            interv: interv,
            sched_interv: sched_interv,
            end: end,
            start: start,
            name: name,
            email:email.is(':checked'),
        };
    }
    function sel_state(obj) {
        return obj.selectmenu('index');
    }






    function obj_equals(x, y) {
        for(p in y) {
            if(typeof(x[p])=='undefined') {return false;}
        }
        for(p in y) {
            if (y[p]) {
                switch(typeof(y[p])) {
                    case 'object':
                        if (!y[p].equals(x[p])) { return false }; break;
                    case 'function':
                        if (typeof(x[p])=='undefined' || (p != 'equals' && y[p].toString() != x[p].toString())) { return false; }; break;
                    default:
                        if (y[p] != x[p]) { return false; }
                }
            }
            else {
                if (x[p]) {
                    return false;
                }
            }
        }
        for(p in x){
            if(typeof(y[p])=='undefined') {return false;}
        }
        return true;
    }


    /* set up the js for a ReportForm */
    function set_up_form(prefix) {
        // based on d1's selection, modify options for d2 and d3 
        $('#id_' + prefix + '-d1').change(
                function(e) {
                    // TODO error?
                    if ($(this).val() != '') {
                        $('#d1Error').hide();
                    }
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
                                           $('#' + prefix + '-reportEditForm-save').button({
                                               label: 'Success...',
                                               disabled: true
                                           });
                                       } else {
                                           console.log(jsonData.errors);
                                           validator.showErrors(jsonData.errors);
                                           $('#' + prefix + '-reportEditForm-save').button({
                                               label: 'Try Again',
                                               disabled: false
                                           });
                                       }
                                   },
                                   error: function(jqXHR, textStatus, errorThrown) {
                                       $('#' + prefix + '-reportEditForm-save').button({
                                           label: 'Try Again',
                                           disabled: false
                                           });
                                       },
                                   beforeSubmit: function(arr, $form, options) {
                                       $('#' + prefix + '-reportEditForm-save').button({label: 'Submitting...',
                                       disabled: true});
                                       }
                                });
                           }
        });

        // Submit form
        $('#' + prefix + '-reportEditForm-save')
            .click(function(e) {
                e.preventDefault();
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


    $("#sched_interval")
        .change(function(e) {
            $('.schedule-help').hide();
            $('.schedule-help.'+$(this).val()).show();
        }).change();

    window.ReportIndexController = ReportIndexController;
})(window.jQuery, window._);
