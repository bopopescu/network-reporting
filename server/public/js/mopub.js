/*
	MoPub Global JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {
		
		/*---------------------------------------/
		/ UI Stuff
		/---------------------------------------*/
		
		// set up buttons
		$('.button').button();
		
		// set up buttonsets
		$('.buttonset').buttonset();
		
		// override default jQuery UI dialog options
		$.extend($.ui.dialog.prototype.options, {
			modal: true,
			resizable: false,
			draggable: false,
			width: 400
		});
		
		// override default jQuery UI datepicker options
		$.datepicker.setDefaults({
			dayNamesMin: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
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
		
		/*---------------------------------------/
		/ Stats Breakdown
		/---------------------------------------*/

		$('.stats-breakdown tr').click(function(e) {
			var row = $(this);
			if(!row.hasClass('active')) {
				var table = row.parents('table');
				$('tr.active', table).removeClass('active');
				row.addClass('active');
			}
		});
		
		/*---------------------------------------/
		/ Highcharts default options
		/---------------------------------------*/

		Highcharts.setOptions({
			chart: {
				animation: false,
				backgroundColor: null,
				borderRadius: 0,
				margin: [30,0,30,45]
			},
			title: { text: null },
			lang: {
				loading: "Loading ..."
			}, 
			credits: { enabled: false },
			style: {
				fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif'
			},
			plotOptions: {
				series: {
					animation: false,
					shadow: false,
					stickyTracking: false
				},
				area: {
					lineWidth: 4,
					fillOpacity: 0.1,
					stacking: 'normal',
					marker: {
						lineWidth: 2,
						radius: 5,
						symbol: 'circle',
						states: {
							hover: {
								lineWidth: 2,
								radius: 7
							}
						}
					},
					states: {
						hover: {
							lineWidth: 4
						}
					}
				}
			},
			xAxis: {
				endOnTick: false,
				gridLineWidth: 0.5,
				gridLineColor: '#dddddd',
				lineWidth: 1,
				lineColor: '#cccccc',
				type: 'datetime',
				labels: {
					style: {
						fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
						color: '#999',
						fontSize: '10px'
					},
					y: 20
				},
				dateTimeLabelFormats: {
					second: '%b %e %l:%M:%S%p',
					minute: '%b %e %l:%M%p',
					hour: '%b %e %l:%M%p',
					day: '%b %e',
					week: '%b %e',
					month: '%b %Y',
					year: '%Y'
				},
				tickColor: '#dddddd',
				tickLength: 5,
				tickWidth: 0.5
			},
			yAxis: {
				showFirstLabel: false,
				showLastLabel: true,
				gridLineWidth: 0.5,
				gridLineColor: '#dddddd',
				min: 0,
				title: {
					text: null
				},
				labels: {
					style: {
						fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
						color: '#999',
						fontSize: '10px'
					},
					x: -5
				}
			},
			legend: {
				borderColor: null,
				borderRadius: 0,
				borderWidth: 0,
				align: 'center',
				verticalAlign: 'top',
				y: -17,
				itemStyle: {
					fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
					size: '12px',
					cursor: 'pointer',
					color: '#444444'
				},
				itemHoverStyle: {
					color: '#e57300'
				},
				itemHiddenStyle: {
					color: '#ccc'
				},
				lineHeight: 12,
				symbolPadding: 6,
				symbolWidth: 12
			},
			tooltip: {
				backgroundColor: "rgba(255, 255, 255, .9)",
				style: {
					fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
					fontSize: '13px',
					padding: '10px'
				}
			}
		});
		
	});
})(this.jQuery);