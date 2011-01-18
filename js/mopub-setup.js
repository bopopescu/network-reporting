/*
	MoPub Dashboard JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {
		
		// Submit button
		$('#appForm-submit')
			.button({ 
				icons: { secondary: "ui-icon-circle-triangle-e" } 
			})
			.click(function(e) {
				e.preventDefault();
				$('#appForm').submit();
		});
		
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

		// Populate ad unit name based on app name
		$('#appForm-name').change(function() {
			var name = $.trim($(this).val());
			$('#appForm-adUnitName').val(name + ' banner ad');
		});
		
		/*---------------------------------------/
		/ Ad Unit Form
		/---------------------------------------*/
		
		// Set up format selection UI
		$('.adForm-formats').each(function() {
			var container = $(this);
			$('input[type="radio"]', container).click(function(e) {
				var radio = $(this);
				var formatContainer = radio.parents('.adForm-format');
				
				$('.adForm-format-image', container).css({ opacity: 0.5 });
				$('.adForm-format-image', formatContainer).css({ opacity: 1 });
				
				if(radio.val() == 'custom') {
					// $('.adForm-format-details input[type="text"]:first', formatContainer).focus();
				}
			}).filter(':checked').click();
			
			$('.adForm-format-image', container).click(function(e) {
				var image = $(this);
				var formatContainer = image.parents('.adForm-format');
				$('input[type="radio"]', formatContainer).click();
			});
			
			$('.adForm-format-details input[type="text"]', container).focus(function() {
				var input = $(this);
				var formatContainer = input.parents('.adForm-format');
				$('input[type="radio"]', formatContainer).click();
			});
		});
	});
})(this.jQuery);