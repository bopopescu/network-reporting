/*
	MoPub Public Site JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {
				
		/*---------------------------------------/
		/ UI
		/---------------------------------------*/
		
		// Header icons
		$('#header-icons a').css({ opacity: 0.25 }).hover(function() {
			$(this).stop().animate({ opacity: 0.75 }, 200);
		}, function() {
			$(this).stop().animate({ opacity: 0.25 }, 400);
		});

	});
})(this.jQuery);
