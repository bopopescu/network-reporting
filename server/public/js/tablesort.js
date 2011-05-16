(function($){
 $(document).ready(function() {
    
     function table_sort(value){
        $('.level0').sort(row_sort(value)).each();
     
     }

     function row_sort(val) {
        function row_sort_help(a, b) {
           var x = a.children('td.'+val)[0].value;
           var y = b.children('td.'+val)[0].value;
           return ((x < y) ? -1 : ((x > y) ? 1 : 0)); 
        }
        return row_sort_help;
     }

     });
 
 })(this.jQuery);
