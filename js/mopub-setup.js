/*
	MoPub Setup Pages JS
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
		
		// Search button
    $('#appForm-search-button')
      .button({ icons: { primary: "ui-icon-search" }, disabled: true})
      .click(function(e) {
        e.preventDefault();
        if ($(this).button( "option", "disabled" ))
          return;

				/*
        $('#searchAppStore-results').append("<img src='/images/loading2.gif' />")
          .append("Loading results...");

        $('#dashboard-searchAppStore-custom-modal').dialog({
          buttons: [
            {
              text: 'Cancel', 
              click: function() {
                $('#searchAppStore-results').html('');
                $(this).dialog("close");
              }
            }
          ]
        });
        var name = $('#appForm input[name="name"]').val();
        var script = document.createElement("script");
        script.src = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch?'       
                       + 'entity=software&limit=10&callback=loadedArtwork&term='+name;
        var head = document.getElementsByTagName("head")[0];
        (head || document.body).appendChild( script );
				*/
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
		$('input[name="appForm-name"]').change(function() {
			var name = $.trim($(this).val());
			$('#appForm-adUnitName').val(name + ' banner ad');
		});
		
		// Toggle enabled/disabled state of search button when app name changes
		$('#appForm-name-ios').keyup(function(e) {
      // Show/hide the app search button
      var name = $.trim($(this).val());
      if (name.length)
        $('#appForm-search-button').button("enable");
      else
        $('#appForm-search-button').button("disable");
      if (e.keyCode == 13) {
        $('#appForm-search-button').click();
      }
    });

		// Change icon
    $('#appForm-changeIcon-link').click(function (e) {
      e.preventDefault();
      $(this).hide();
      $('#appForm-icon-upload').show();
      $('#appForm input[name="img_url"]').val('');
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