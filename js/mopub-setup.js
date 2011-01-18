/*
	MoPub Dashboard JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {
		
		/*---------------------------------------/
		/ App Details Form
		/---------------------------------------*/
		
		// Platform-dependent URL/package name switching
		$('#appForm input[name="appForm-platform"]').click(function(e) {
			$('#appForm .appForm-platformDependent')
				.removeClass('ios')
				.removeClass('android')
				.addClass($(this).val());
		}).filter(':checked').click(); // make sure we're in sync when the page loads


	});
})(this.jQuery);