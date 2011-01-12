/*
	MoPub Global JS
*/

(function($){
	// dom ready
	$(document).ready(function() {
		
		// set up buttonsets
		$('.buttonset').buttonset();
		
		// set up dateOptions
		$('.dateOptions input').click(function() {
			var option = $(this).val();
			if(option == 'custom') {
				alert('Custom');
			}
			else {
				// do something with selected option ...
			}
		});
		
	});
})(this.jQuery);