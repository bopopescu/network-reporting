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
     });

 })(this.jQuery);
