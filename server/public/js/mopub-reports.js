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

    $('#reports-view-editReportButton').button({icons: {primary: 'ui-icon-circle-plus'}})
        .click(function(e) {
                e.preventDefault();
                //get key
                //var report_form = get form
                report_form.dialog({width:1000});
                });
 });
})(this.jQuery);
