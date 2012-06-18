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

    var sub_label;
    if (window.location.pathname == '/reports/') {
        sub_label = 'Run';
    }
    else {
        sub_label = 'Save';
    }

    $('#reportCreateForm-submit')
    .button({
        label: sub_label,
        icons: {secondary: 'ui-icon-circle-triangle-e' }})
    .click(function(e) {
            e.preventDefault();
            if (rep_validate($('#reportCreateForm'))) {
                $('#reportCreateForm').submit();
            }
            else {
                $('#formError').show();
            }
    });

    $('#reports-view-runReportButton').button({
        icons: {secondary: 'ui-icon-circle-triangle-e' }});

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
             $('#reportCreateForm-submit').button({label: 'Save As'});
             $('#sched_interval').selectmenu('index', 0).change();
             $('#reportForm-container').dialog({width:750});
        });


     $('#reportCreateForm-cancel').button()
         .click(function(e) {
             e.preventDefault();
             $('#reports-reportAddForm').slideUp('fast');
         });

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

     var ReportIndexController = {
         initialize: function(bootstrapping_data) {
             var report_keys = bootstrapping_data.report_keys;

             _.each(report_keys, function(key) {
                 var row = $('#' + key + '-row')

                 $(row).mouseenter(function(e) {
                     $('#' + key + '-edit-link').show();
                 })
                 $(row).mouseleave(function(e) {
                     $('#' + key + '-edit-link').hide();
                 })

                 $('#' + key + '-edit-link')
                     .click(function(e) {
                         e.preventDefault();
                         $('#' + key + '-saveAs').val('False');
                         $('#' + key + '-reportCreateForm-submit').button({label: 'Save'});
                         var report_form = $('#' + key + '-reportForm-container');
                         report_form.dialog({width:750});
                     });

                 $('#' + key + '-reportCreateForm-cancel')
                     .click(function(e) {
                         e.preventDefault();
                         $('.dim-selectmenu').selectmenu('enable');
                         $('#interval').selectmenu('enable');
                         $('#start-input').xdatepicker('enable');
                         $('#end-input').xdatepicker('enable');
                         revert_state(form_state);
                         $('#' + key + '-reportForm-container').dialog('close');
                     });

            });
         }
     }


     $('#reportUpdateForm-cancel')
         .button()
         .click(function(e) {
             e.preventDefault();
             $(this).parents('#reportFormSaveAs-container')
                 .dialog('close');
         });

     $('#reportUpdateForm-submit')
         .button()
         .click(function(e) {
             e.preventDefault();
            if($('#start-input').xdatepicker('isDisabled')) {
                $('#start-input').xdatepicker('enable');
            }
            if($('#end-input').xdatepicker('isDisabled')) {
                $('#end-input').xdatepicker('enable');
            }
            $(this).parents('form').submit();
         });

     $('#reports-view-exportSelect')
         .change(function(e) {
             e.preventDefault();
             var val = $(this).val();
             if (val != 'exp') {
                 $('#reportExportForm')
                     .find('#report-exportFtype')
                     .val(val)
                     .end()
                     .submit();
             }
             $(this).selectmenu('index', 0);
        });

    $('#reports-view-exportSelect-menu').find('li').first().hide();

    $('#reports-view-exportButton')
        .click(function(e) {
            e.preventDefault();
            $('#reportExportForm').submit();
        });



    $('.int-selectmenu').selectmenu({
        style: 'popup',
        maxHeight:300,
        width:115
    });

    $('#sched_interval').selectmenu({
        style:'popup',
        maxHeight:300,
        width:135,
    });

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

    var selects = $('.dim-selectmenu').selectmenu({
        style: 'popup',
        maxHeight:320,
        width:110
    });

    d1_sel = $(selects[0]);
    d2_sel = $(selects[1]);
    d3_sel = $(selects[2]);

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

    function get_form_state() {
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
    //Get the state of the form so we go back to this on cancel
    var form_state = get_form_state();


    $('#d1').change(
        function(e) {
            if ($(this).val() != '') {
                $('#d1Error').hide();
            }
            e.preventDefault();
            d1_validate($(this));
            d2_validate($('#d2'));
        }).change();


    function d1_validate(obj) {
            var idx = obj.selectmenu('index');
            //start with everything enabled
            for (var i = 0; i < 14; i++) {
                d3_sel.selectmenu('enable', i);
                d2_sel.selectmenu('enable', i);
            }
            var d2_idx = d2_sel.selectmenu("index");
            var d3_idx = d3_sel.selectmenu("index");
            $('#d2-show').show();
            switch(obj.val()) {
                case '':
                    d2_sel.selectmenu("index", 0);
                    d3_sel.selectmenu("index", 0);
                    $('#d2-show').hide();
                    $('#d3-show').hide();
                    break;
                case 'adunit':
                    if (d2_idx == 2) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 2) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '2');
                    d3_sel.selectmenu('disable', '2');

                case 'app':
                    if (d2_idx == 1) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 1) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '1');
                    d3_sel.selectmenu('disable', '1');
                    break;

                case 'creative':
                    if (d2_idx == 5) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 5) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '5');
                    d3_sel.selectmenu('disable', '5');

                case 'campaign':
                    if (d2_idx == 4) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 4) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '4');
                    d3_sel.selectmenu('disable', '4');

                case 'priority':
                    if (d2_idx == 3) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 3) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '3');
                    d3_sel.selectmenu('disable', '3');
                    break;
                case 'hour':
                    if (d2_idx == 9) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 9) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '9');
                    d3_sel.selectmenu('disable', '9');
                case 'day':
                    if (d2_idx == 8) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 8) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '8');
                    d3_sel.selectmenu('disable', '8');
                case 'week':
                    if (d2_idx == 7) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 7) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '7');
                    d3_sel.selectmenu('disable', '7');
                case 'month':
                    if (d2_idx == 6) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 6) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '6');
                    d3_sel.selectmenu('disable', '6');
                    break;
                case 'country':
                    if (d2_idx == 10) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 10) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '10');
                    d3_sel.selectmenu('disable', '10');
                    break;
                case 'marketing':
                    if (d2_idx == 11) {
                        d2_sel.selectmenu('index', 0);
                    }
                    if (d3_idx == 11) {
                        d3_sel.selectmenu('index', 0);
                    }
                    d2_sel.selectmenu('disable', 11);
                    d3_sel.selectmenu('disable', 11);
                    break;
                case 'os_ver':
                    if (d2_idx == 13) {
                        d2_sel.selectmenu('index', 0);
                    }
                    if (d3_idx == 13) {
                        d3_sel.selectmenu('index', 0);
                    }
                    d2_sel.selectmenu('disable', 13);
                    d3_sel.selectmenu('disable', 13);
                case 'os':
                    if (d2_idx == 12) {
                        d2_sel.selectmenu('index', 0);
                    }
                    if (d3_idx == 12) {
                        d3_sel.selectmenu('index', 0);
                    }
                    d2_sel.selectmenu('disable', 12);
                    d3_sel.selectmenu('disable', 12);
                    break;
                default:
                    break;
            }
    }

    $('#d2').change(
        function(e) {
            e.preventDefault();
            d1_validate($('#d1'));
            d2_validate($(this));
        });

    $('.update-button').change(
        function(e) {
            e.preventDefault();
            if (!obj_equals(form_state, get_form_state())) {
                $('#reportCreateForm-submit').button({label:'Save and Run'});
            }
            else {
                $('#reportCreateForm-submit').button({label:'Save'});
            }
        }).change();



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




     function d2_validate(obj) {
         var idx = obj.selectmenu('index');
        //start with everything enabled
        var d3_idx = d3_sel.selectmenu("index");
        $('#d3-show').show();
        switch(obj.val()) {
            case '':
                d3_sel.selectmenu("index", 0);
                $('#d3-show').hide();
                break;
            case 'adunit':
                if (d3_idx == 2) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '2');
            case 'app':
                if (d3_idx == 1) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '1');
                break;

            case 'creative':
                if (d3_idx == 5) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '5');
            case 'campaign':
                if (d3_idx == 4) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '4');
            case 'priority':
                if (d3_idx == 3) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '3');
                break;

            case 'hour':
                if (d3_idx == 9) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '9');
            case 'day':
                if (d3_idx == 8) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '8');
            case 'week':
                if (d3_idx == 7) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '7');
            case 'month':
                if (d3_idx == 6) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '6');
                break;
            case 'country':
                if (d3_idx == 10) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '10');
                break;
            case 'marketing':
                if (d3_idx == 11) {
                    d3_sel.selectmenu('index', 0);
                }
                d3_sel.selectmenu('disable', 11);
                break;
            case 'os_ver':
                if (d3_idx == 13) {
                    d3_sel.selectmenu('index', 0);
                }
                d3_sel.selectmenu('disable', 13);
            case 'os':
                if (d3_idx == 12) {
                    d3_sel.selectmenu('index', 0);
                }
                d3_sel.selectmenu('disable', 12);
                break;
            default:
                break;
        }
    }


    $("#sched_interval")
    .change(function(e) {
        $('.schedule-help').hide();
        $('.schedule-help.'+$(this).val()).show();
    }).change();

    $("#email-input-checkbox")
    .change(function(e) {
        if ($(this).attr('checked')) {
            $('#email-recipients').show();
        } else {
            $('#email-recipients').hide();
        }
    }).change();

    $('#reportStateChangeForm-delete')
        .click(function(e) {
            e.preventDefault();
            $('#reportStateChangeForm').find('#action').val('delete').end().submit();
        });

    window.ReportIndexController = ReportIndexController;
})(window.jQuery, window._);
