/*
	MoPub Dashboard JS
*/

(function($){
	// dom ready
	$(document).ready(function() {
		
		// set up buttons
		$('#dashboard-apps-addAppButton').button({ icons: { primary: "ui-icon-circle-plus" } });
		$('#dashboard-apps-toggleAllButton')
			.button({ 
				icons: { primary: "ui-icon-triangle-2-n-s" } 
			})
			.click(function(e) {
				e.preventDefault();
		});
		
		// set up showing/hiding of app details
		$('.appData-details').each(function() {
			var details = $(this);
			var data = $('.appData-details-inner', details);
			var button = $('.appData-details-toggleButton', details);
			
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
		});
		
		// set up toggle all app details button
		$('#dashboard-apps-toggleAllButton').click(function(e) {
			e.preventDefault();
			var hiddenAppDetails = $('.appData-details .hide').parents('.appData-details');
			var shownAppDetails = $('.appData-details .show').parents('.appData-details');
			if(hiddenAppDetails.length > 0) {
				hiddenAppDetails.each(function() {
					$('.appData-details-toggleButton', $(this)).click();
				});
			}
			else {
				shownAppDetails.each(function() {
					$('.appData-details-toggleButton', $(this)).click();
				});
			}
		});

	});
})(this.jQuery);