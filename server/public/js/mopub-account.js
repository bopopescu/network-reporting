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
				$('#accountForm').submit();
		});
		
		// set up showing/hiding of app details
		$('.adForm').each(function() {
			var details = $(this);
			var data = $('.formFields', details);
			var button = $('.adForm-fields-toggleButton', details);
			var infobutton = $('.adForm-fields-infoButton', details);
			
			function getButtonTextElement() {
				var buttonTextElement = $('.ui-button-text', button);
				if(buttonTextElement.length == 0) buttonTextElement = button;
				return buttonTextElement;
			}

			function didShowData() {
				data.removeClass('hide');
				data.addClass('show');
				button.button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
				getButtonTextElement().text('Hide details');
			}
			
			function didHideData() {
				data.removeClass('show');
				data.addClass('hide');
				button.button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
				getButtonTextElement().text('Show details');
			}

			if(data.hasClass('show')) {
				didShowData();
			}
			else {
				data.hide();
				didHideData();
			}
			
			button.click(function(e) {
				e.preventDefault();
				if(data.hasClass('show')) {
					data.slideUp('fast');
					didHideData();
				}
				else {
					data.slideDown('fast');
					didShowData();
				}
			});
			
			infobutton.button({ 
				icons: { secondary: "ui-icon-info" } 
			})
			.click(function(e) {
				e.preventDefault();
				$('#accountInfoForm').dialog({
				  width: 570,
					buttons: [
						{
							text: 'Close', 
							click: function() {
								$(this).dialog("close");
							}
						}
					]
				});
			});
		});
	});
})(this.jQuery);