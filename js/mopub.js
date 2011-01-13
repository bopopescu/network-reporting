/*
	MoPub Global JS
*/

(function($){
	// dom ready
	$(document).ready(function() {
		
		/*---------------------------------------/
		/ UI Stuff
		/---------------------------------------*/
		
		// set up buttonsets
		$('.buttonset').buttonset();
		
		// set up dateOptions
		$('.dateOptions input').click(function() {
			var option = $(this).val();
			if(option == 'custom') {
				alert('Custom');
			}
			else {
				// TODO: tell server about selected option to get new data
			}
		});
		
		// override default jQuery UI dialog options
		$.extend($.ui.dialog.prototype.options, {
			modal: true,
			resizable: false,
			draggable: false,
			width: 400
		});
		
		/*---------------------------------------/
		/ Message Center
		/---------------------------------------*/
		
		// hide message center when page loads if there are no messages
		function hideMessageCenterIfNoMessages() {
			if($('.messageCenter-message').length == 0) {
				$('#messageCenter').hide();
			}
		}
		hideMessageCenterIfNoMessages();
		
		// set up "More info" links
		$('.messageCenter-message-moreInfoLink').click(function(e) {
			e.preventDefault();
			var link = $(this);
			var info = $('.messageCenter-message-moreInfo', link.parents('.messageCenter-message'));
			// clone info (so the original doesn't get moved around) and make the dialog
			info.clone().dialog({ 
				buttons: { "Close": function() { $(this).dialog("close"); } }, 
				close: function(e, u) { $(this).remove(); } // remove clone
			});
		});
		
		// set up "Hide this" links
		$('.messageCenter-message-hide').click(function(e) {
			e.preventDefault();
			var link = $(this);
			var message = link.parents('.messageCenter-message');
			message.fadeOut('fast', function() {
				message.remove();
				hideMessageCenterIfNoMessages();
			});
			// TODO: tell server that message.attr('id') has been hidden
		});
		
	});
})(this.jQuery);