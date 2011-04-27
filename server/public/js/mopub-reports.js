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
    $('input[name="start"]').datepicker({ minDate:0 });
    $('input[name="end"]').datepicker({ minDate:0 });

    $('#reportCreateForm-submit')
    .button({
        icons: {secondary: 'ui-icon-circle-triangle-e' }})
    .click(function(e) {
            e.preventDefault();
            $('#reportCreateForm').submit();
    });

 });
})(this.jQuery);
