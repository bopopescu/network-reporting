/*
	MoPub Global JS
*/

//For JSLint Validation:
/*global console: true, Highcharts: true*/

//mopub singleton object
var mopub = mopub || {};
mopub.utils = mopub.utils || {};

(function($){
	// dom ready
	$(document).ready(function() {
		/*---------------------------------------/
		/ UI Stuff
		/---------------------------------------*/
		
		// preload images (defined below)
		var JQUERY_UI_IMAGE_PATH = '/js/mylibs/jquery-ui-1.8.7.custom/css/mopub/images';
		$.preLoadImages(
			'/images/ui/ui-button-active.png',
			'/images/ui/ui-button-default.png',
			'/images/ui/ui-button-hover.png',
			'/images/ui/ui-icons-active.png',
			'/images/ui/ui-icons-focus.png',
			'/images/ui/ui-icons-hover.png',
			'/images/ui/ui-icons-progress.png',
			JQUERY_UI_IMAGE_PATH + '/ui-bg_highlight-hard_25_e57300_1x100.png',
			JQUERY_UI_IMAGE_PATH + '/ui-bg_highlight-hard_50_dddddd_1x100.png',
			JQUERY_UI_IMAGE_PATH + '/ui-bg_highlight-hard_100_f3f3f3_1x100.png',
			JQUERY_UI_IMAGE_PATH + '/ui-bg_inset-soft_25_595959_1x100.png',
			JQUERY_UI_IMAGE_PATH + '/ui-icons_0090d9_256x240.png',
			JQUERY_UI_IMAGE_PATH + '/ui-icons_cc2929_256x240.png',
			JQUERY_UI_IMAGE_PATH + '/ui-icons_ffffff_256x240.png'
		);
		
		// replace <legend> with <h2>
		$('legend').each(function() {
			var legend = $(this);
			var h2 = $('<h2>'+legend.html()+'</h2>');
			h2.attr('class', legend.attr('class'));
			h2.attr('id', legend.attr('id'));
			legend.replaceWith(h2);
		});
		
		// set up buttons
		$('.button').button().css({ visibility: 'visible' });
		
		// set up buttonsets
		$('.buttonset').buttonset().css({ visibility: 'visible' });
		
		// gray out any buttonsets that ought to be disabled
		$('.buttonset-start-disabled').buttonset()
		$('.buttonset-start-disabled').buttonset({ disabled: true });
		
		// set up selectmenus
		$('.selectmenu').selectmenu().css({ visibility: 'visible' });
		
		// set up validation to be run on form submit
        $('.validate').validate();
		
		// set up treeview
    // $(".treeview").treeview({
    //        animated: "fast",
    //        collapsed: true,
    //        unique: true,
    //        persist: "cookie",
    //        })
    // 
    
    $(".tree").treeview()
		
		
		
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
		
		// set up form placeholders
		$('input[placeholder], textarea[placeholder]').placeholder({ preventRefreshIssues: true });
		
		// set up text overflow elements
		$('#titlebar .breadcrumb h1, .dataTable-name .inner').textOverflow(' &hellip;');
		
		/*---------------------------------------/
		/ Tooltips
		/---------------------------------------*/

		$.fn.qtip.styles.mopub = { 
			background: '#303030',
			color: '#ffffff',
			border: {
				radius: 5
			},
			tip: {
				size: {
					x: 10,
					y: 10
				}
			},
			name: 'dark' // Inherit the rest of the attributes from the preset dark style
		};

		$('a[title]').qtip({ style: { name: 'mopub', tip: true } });
		$('.formFields-field-help-link[title]').click(function(e) { e.preventDefault(); });
		
		/*---------------------------------------/
		/ Message Center
		/---------------------------------------*/
		
		// hide message center when page loads if there are no messages
		function hideMessageCenterIfNoMessages() {
			if($('.messageCenter-message').length === 0) {
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

	/*---------------------------------------/
	/ What's This?-ifier 
	/---------------------------------------*/

      $('.whatsthis').click(function(e) {
          e.preventDefault();
          $('#'+$(this).attr('id').replace('helpLink', 'helpContent')).dialog({
            buttons: { "Close": function() { $(this).dialog('close');} }
          });
      });
		
	});
	
	/*---------------------------------------/
	/ Image Preloader
	/---------------------------------------*/
	
  var cache = [];
  // Arguments are image paths relative to the current page.
  $.preLoadImages = function() {
    var args_len = arguments.length;
    for (var i = args_len; i--;) {
      var cacheImage = document.createElement('img');
      cacheImage.src = arguments[i];
      cache.push(cacheImage);
    }
    // Commented out for cleanliness
    // log(cache); 
  };
  
  // helper fn for console logging
  var log;

  if (window.console && typeof console.log === "function"){
    // use apply to preserve context and invocations with multiple arguments
    log = function () { console.log.apply(console, arguments); };
  } else {
    log = function(){ return; }
  }
  
  /*---------------------------------------/
  / Utility functions.
  /---------------------------------------*/
  
  mopub.utils.formatNumberWithCommas = function(string) {
    string += '';
    x = string.split('.');
    x1 = x[0];
    x2 = x.length > 1 ? '.' + x[1] : '';
    var rgx = /(\d+)(\d{3})/;
    while (rgx.test(x1)) {
      x1 = x1.replace(rgx, '$1' + ',' + '$2');
    }
    return x1 + x2;
  };
  
  mopub.utils.formatNumberAsPercentage = function(string) {
    // We round to two decimal places.
    return (string*100).toFixed(2) + '%';
  };
  
})(this.jQuery);

// =====================================================================
// mopub.utils.AjaxChunkedFetch
// =====================================================================

(function(utils, $) {
  
  var AjaxChunkedFetch = utils.AjaxChunkedFetch = function(args) {
    this.items = {};
    this.chunkComplete = function(data, chunk, fetchObj) {};
    this.chunkFailure = function(chunk, fetchObj) {};
    this.fetchComplete = function(fetchObj) {};
    this.isComplete = false;
    this.hasFailed = false;
    $.extend(this, args);

    this.unfetchedItems = {};
    var self = this;
    $.each(this.items, function(index, item) { self.unfetchedItems[item] = {}; });

    return this;
  };
  
  AjaxChunkedFetch.chunkArray = function(array, chunkSize) {
    if (!array) return [];

    var chunks = [];
    $.each(array, function(index, elem) {
      var chunkNumber = Math.floor(index / chunkSize);
      var indexInChunk = index % chunkSize;
      chunks[chunkNumber] = chunks[chunkNumber] || [];
      chunks[chunkNumber][indexInChunk] = elem;
    });
    return chunks;
  };
  
  // Time to wait before terminating AJAX request.
  AjaxChunkedFetch.TIMEOUT_MILLISECONDS = 10000;

  // Maximum number of AJAX retries before giving up.
  AjaxChunkedFetch.MAX_FAILED_ATTEMPTS = 3;

  // Number of items to be fetched in a single AJAX request.
  AjaxChunkedFetch.DEFAULT_CHUNK_SIZE = 8;

  // Time to wait before retrying a failed AJAX request.
  AjaxChunkedFetch.BACKOFF_TIME_MILLISECONDS = 1000;

  // Multiplier to increase the backoff time when there are consecutive failures.
  AjaxChunkedFetch.BACKOFF_MULTIPLIER = 1.5;

  AjaxChunkedFetch.prototype.unfetchedItemsEmpty = function() {
    for (var key in this.unfetchedItems) { 
      if (this.unfetchedItems.hasOwnProperty(key)) return false;
    }
    return true;
  };

  AjaxChunkedFetch.prototype.start = function() {
    this.isComplete = false;
    this.hasFailed = false;
    
    if (!this.urlConstructor) {
      this.hasFailed = true;
      this.chunkFailure([], this);
      return;
    }

    var chunks = AjaxChunkedFetch.chunkArray(this.items, 
      AjaxChunkedFetch.DEFAULT_CHUNK_SIZE);
    if (chunks.length <= 0) {
      this.isComplete = true;
      this.fetchComplete(this);
      return;
    }
    
    var self = this;
    $.each(chunks, function(index, chunk) {
      var request = new FetchRequest({
        items: chunk,
        url: self.urlConstructor(chunk, self),
        success: self.chunkComplete,
        failure: self.chunkFailure,
        fetchObject: self
      });
      request.execute();
    });
  };

  AjaxChunkedFetch.prototype.markItemsComplete = function(items) {
    var self = this;
    $.each(items, function(index, item) {
      delete self.unfetchedItems[item];
    });

    if (this.unfetchedItemsEmpty()) {
      this.isComplete = true;
      this.hasFailed = false;
      this.fetchComplete(this);
    }
  };
  
  AjaxChunkedFetch.prototype.markAsFailed = function() {
    this.hasFailed = true;
  };
  
  // =====================================================================
  
  var FetchRequest = AjaxChunkedFetch.FetchRequest = function(args) {
    this.items = [];
    this.url = "";
    this.success = function(data) {};
    this.failure = function() {};
    this.backoffData = new BackoffData();
    $.extend(this, args);
    return this;
  };

  FetchRequest.prototype.execute = function() {
    var self = this;

    $.ajax({
      url: self.url,
      dataType: 'json',
      success: function() {
        return function(data) {
          self.success(data, self.items, self.fetchObject);
          self.fetchObject.markItemsComplete(self.items);
        };
      }(),
      error: function() {
        self.backoffData.failedAttempts++;
        if (self.backoffData.failedAttempts > AjaxChunkedFetch.MAX_FAILED_ATTEMPTS) {
          self.failure(self.items, self.fetchObject);
          self.fetchObject.markAsFailed();
          // TODO: mark items as failed in self.fetchObject.
        } else {
          // Schedule retry and extend the backoff delay.
          setTimeout(function() { self.execute() }, self.backoffData.delay);
          self.backoffData.delay *= AjaxChunkedFetch.BACKOFF_MULTIPLIER;
        }
      },
      timeout: AjaxChunkedFetch.TIMEOUT_MILLISECONDS
    });
  };
  
  // =====================================================================
  
  var BackoffData = AjaxChunkedFetch.BackoffData = function(args) {
    this.delay = AjaxChunkedFetch.BACKOFF_TIME_MILLISECONDS;
    this.failedAttempts = 0;
    $.extend(this, args);
    return this;
  };
  
})(mopub.utils = mopub.utils || {}, this.jQuery);

// =====================================================================

function obj_equals(x, y) {
    for(p in y) {
        if(typeof(x[p])=='undefined') {return false;}
    }
    for(p in y) {
        if (y[p]) {
            switch(typeof(y[p])) {
                case 'object':
                    if (!y[p].equals(x[p])) { return false }; break;
                case 'function':
                    if (typeof(x[p])=='undefined' || (p != 'equals' && y[p].toString() != x[p].toString())) { return false; }; break;
                default:
                    if (y[p] != x[p]) { return false; }
            }
        }
        else {
            if (x[p]) {
                return false;
            }
        }
    }
    for(p in x){
        if(typeof(y[p])=='undefined') {return false;}
    }
    return true;
}

