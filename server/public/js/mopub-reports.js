(function($) {
 
 $(document).ready(function() {

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
    $('input[name="start"]').datepicker();
    $('input[name="end"]').datepicker();

    $('#reportCreateForm-submit')
    .button({
        icons: {secondary: 'ui-icon-circle-triangle-e' }})
    .click(function(e) {
            e.preventDefault();
            $('#reportCreateForm').submit();
    });

    $('#reports-view-runReportButton').button({
        icons: {secondary: 'ui-icon-circle-triangle-e' }})

    $('#reports-view-saveReportButton')
    .button({
        icons: {secondary: 'ui-icon-circle-check'}})
    .click(function(e) {
        e.preventDefault();
        console.log("clicky");
        $.ajax({url:'http://' + window.location.host + '/reports/save/' + $('#reportKey').val() + '/'})
    })

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

    $('#reports-view-editReportButton').button({icons: {primary: 'ui-icon-wrench'}})
        .click(function(e) {
            e.preventDefault();
            var report_form = $('#reportForm-container');
            report_form.dialog({width:750});
        });

    $('#reports-view-saveAsReportButton').button({icons: {secondary: 'ui-icon-check'}})
        .click(function(e) {
            e.preventDefault();
            $('#reportFormSaveAs-container').dialog({width:750});
        });

    $('#reportCreateForm-cancel')
        .button()
        .click(function(e) {
            e.preventDefault();
            $(this).parents('#reportForm-container')
            .dialog('close');
        });

    $('#reportUpdateForm-cancel')
        .button()
        .click(function(e) {
            e.preventDefault();
            $(this).parents('#reportFormSaveAs-container')
            .dialog('close');
        });

    $('#reportCreateForm-submit')
        .button()
        .click(function(e) {
            e.preventDefault();
            $(this).parents('form').submit();
        });

    $('#reportUpdateForm-submit')
        .button()
        .click(function(e) {
            e.preventDefault();
            $(this).parents('form').submit();
        });


    $('.int-selectmenu').selectmenu({
        style: 'popup',
        maxHeight:300,
        width:115
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
                var one_day = 1000*60*60*24
                switch (val) {
                    case 'today':
                        var dte = format_date(today); 
                        $('#end-input').val(dte);
                        $('#start-input').val(dte);
                        break;
                    case 'yesterday':
                        today.setTime(today.getTime() - one_day);
                        var dte = format_date(today); 
                        $('#end-input').val(dte);
                        $('#start-input').val(dte);
                        break;
                    case '7days':
                        var dte = format_date(today); 
                        $('#end-input').val(dte);
                        today.setTime(today.getTime() - (7*one_day));
                        dte = format_date(today); 
                        $('#start-input').val(dte);
                        break;
                    case 'lmonth':
                        var this_mo = today.getMonth();
                        while (today.getMonth() == this_mo) {
                            today.setTime(today.getTime() - one_day);
                        }
                        var dte = format_date(today); 
                        $('#end-input').val(dte);
                        today.setDate(1);
                        dte = format_date(today); 
                        $('#start-input').val(dte);
                        break;
                }
            }
            else {
                return;
            }
        }).change();

    $('.date-field')
        .focus(function(e) {
            update = true;
        })
        .change(function(e) {
            if (update) {
                $('#interval').selectmenu('index', 4);
            }
            else {
                update = true;
                return;
            }
        });

    var selects = $('.dim-selectmenu').selectmenu({
        style: 'popup',
        maxHeight:300,
        width:100
    });

    d1_sel = $(selects[0]);
    d2_sel = $(selects[1]);
    d3_sel = $(selects[2]);

    $('#d1').change(
        function(e) {
            e.preventDefault();
            d1_validate($(this));
            d2_validate($('#d2'));
        });


    function d1_validate(obj) {
            var idx = obj.selectmenu('index');
            //start with everything enabled
            for (var i = 0; i < 11; i++) {
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
                    if (d2_idx == 4) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 4) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '4');
                    d3_sel.selectmenu('disable', '4');

                case 'campaign':
                    if (d2_idx == 3) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 3) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '3');
                    d3_sel.selectmenu('disable', '3');

                case 'priority':
                    if (d2_idx == 5) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 5) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '5');
                    d3_sel.selectmenu('disable', '5');
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
                if (d3_idx == 4) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '4');
            case 'campaign':
                if (d3_idx == 3) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '3');
            case 'priority':
                if (d3_idx == 5) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '5');
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
            default:
                break;
        }
    }
 });
})(this.jQuery);
