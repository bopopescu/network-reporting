/*
	MoPub Dashboard JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {
		
		// Submit button
		$('#accountForm-submit')
			.button({ 
				icons: { secondary: "ui-icon-circle-triangle-e" } 
			})
			.click(function(e) {
				e.preventDefault();
				alert('hello');
				$('#accountForm').submit();
		});
	});
})(this.jQuery);