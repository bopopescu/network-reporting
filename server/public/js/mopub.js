/*
	MoPub Global JS
*/

//For JSLint Validation:
/*global console: true, Highcharts: true*/

//mopub singleton object
var mopub = mopub || {};
mopub.Utils = mopub.Utils || {};

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
  
  mopub.Utils.formatNumberWithCommas = function(string) {
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
  
  mopub.Utils.formatNumberAsPercentage = function(string) {
    // We round to two decimal places.
    return (string*100).toFixed(2) + '%';
  };
  
  mopub.Utils.getKeysFromObject = function(object) {
    var keys = [];
    for (var key in object) {
      if (object.hasOwnProperty(key)) keys.push(key);
    }
    return keys;
  };
  
})(this.jQuery);

// =====================================================================
// mopub.Utils.AjaxChunkedFetch
// =====================================================================

(function(Utils, $) {
  
  var AjaxChunkedFetch = Utils.AjaxChunkedFetch = function(args) {
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
  
  AjaxChunkedFetch.prototype.retry = function() {
    // TODO: this might be called before all fetch requests have finished, which can result in
    // some items being fetched unnecessarily.
    
    if (!this.hasFailed) return;
    
    var unfetched = mopub.Utils.getKeysFromObject(this.unfetchedItems);
    if (unfetched.length <= 0) return;
    
    var chunks = AjaxChunkedFetch.chunkArray(unfetched, 
      AjaxChunkedFetch.DEFAULT_CHUNK_SIZE);
    
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
  
})(mopub.Utils = mopub.Utils || {}, this.jQuery);

// =====================================================================
// mopub.Stats
// =====================================================================

(function(Stats, $) {
  
  Stats.sortStatsObjectsByStat = function(objects, statName) {
    objects.sort(function(a, b) {
      var statA = parseFloat(a["stats"]["sum"][statName]);
      var statB = parseFloat(b["stats"]["sum"][statName]);
      if (statA < statB) return 1;
      if (statA > statB) return -1;
      else return 0;
    });
    return objects;
  };
  
  Stats.statArrayFromDailyStats = function(arrayOfDailyStats, statName) {
    return $.map(arrayOfDailyStats, function(oneDayStats) {
      return parseFloat(oneDayStats[statName]);
    });
  };
  
  Stats.getGraphSummedStatsForStatName = function(statName, objects) {
    var result = [];
    
    var topThreePerformers = objects.splice(0, 3);
    var otherPerformers = objects;
  
    // Get stats for the top three performers.
    $.each(topThreePerformers, function(index, statsObject) {
      var name = statsObject["key"];
      var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
      var graphStatsObject = {};
      graphStatsObject[name] = Stats.statArrayFromDailyStats(arrayOfDailyStats, statName);
      result.push(graphStatsObject);
    });
  
    if (otherPerformers.length == 0) return result;
  
    // Get stats for all other performers.
    var statsForOtherPerformers = Stats.sumDailyStatsAcrossStatsObjects(otherPerformers, statName);
    var otherDict = { "Others": statsForOtherPerformers };
    result.push(otherDict);
  
    return result;
  };

  Stats.sumDailyStatsAcrossStatsObjects = function(objects, statName) {
    var result = [];
    $.each(objects, function(index, statsObject) {
      var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
      $.each(arrayOfDailyStats, function(dayIndex, oneDayStats) {
        if (!result[dayIndex]) result[dayIndex] = 0;
        result[dayIndex] += parseFloat(oneDayStats[statName]);
      });
    });
    return result;
  };
  
  Stats.getGraphCtrStats = function(objects) {
    var result = [];
  
    var topThreePerformers = objects.splice(0, 3);
    var otherPerformers = objects;
    
    // Get stats for the top campaigns.
    $.each(topThreePerformers, function(index, statsObject) {
      var name = statsObject["key"];
      var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
      var graphStatsObject = {};
      graphStatsObject[name] = Stats.statArrayFromDailyStats(arrayOfDailyStats, "ctr");
      result.push(graphStatsObject);
    });
  
    if (otherPerformers.length == 0) return result;
  
    // Get stats for all other campaigns.
    var statsForOtherPerformers = Stats.getDailyCtrAcrossStatsObjects(otherPerformers);
    var otherDict = { "Others": statsForOtherPerformers };
    result.push(otherDict);
    
    return result;
  };
  
  Stats.getDailyCtrAcrossStatsObjects = function(objects) {
    var ctr = [];
    var clicks = Stats.sumDailyStatsAcrossStatsObjects(objects, "click_count");
    var impressions = Stats.sumDailyStatsAcrossStatsObjects(objects, "impression_count");
  
    for (var i = 0; i < clicks.length; i++) {
      ctr[i] = (clicks[i] / impressions[i]) || 0;
    }
    return ctr;
  };
  
})(mopub.Stats = mopub.Stats || {}, this.jQuery);

// =====================================================================
// mopub.Chart
// =====================================================================

(function(Chart, $) {
  
  Chart.setupDashboardStatsChart = function(seriesType) {
    // get active metric from breakdown
    var metricElement = $('#dashboard-stats .stats-breakdown .active');
    if (metricElement === null || metricElement.length === 0) return;
    var metricElementIdComponents = metricElement.attr('id').split('-');
    var activeMetric = metricElementIdComponents[metricElementIdComponents.length - 1];

    // get data
    var data = mopub.dashboardStatsChartData;
    if (typeof data == 'undefined') {
      Chart.chartError();
      return;
    }
    
    // set up series
    var colors = ['#0090d9', '#e57300', '#53a600', '#444444'];
    var chartSeries = [];
    var activeData = data[activeMetric];
    if (typeof activeData == 'undefined') {
      Chart.chartError();
      return;
    }
    
    $.each(activeData, function(i, seriesObject) {
      var seriesName, seriesData, seriesLineWidth;
      
      $.each(seriesObject, function(name, value) {
        seriesName = name;
        seriesData = value;
        
        if (seriesType == 'line' && activeMetric == 'ctr') {
          seriesLineWidth = (seriesName == 'MoPub Optimized') ? 3 : 2;
        } else seriesLineWidth = 4;
      });
      
      chartSeries.push({
        name: seriesName,
        data: seriesData,
        color: colors[i],
        lineWidth: seriesLineWidth
      });
    });

    // setup HighCharts chart
    this.trafficChart = new Highcharts.Chart({
      chart: {
        renderTo: 'dashboard-stats-chart',
        defaultSeriesType: seriesType,
        marginTop: 0,
        marginBottom: 55
      },
      plotOptions: {
        series: {
          pointStart: data.pointStart,
          pointInterval: data.pointInterval
        }
      },
      legend: {
        verticalAlign: "bottom",
        y: -7,
        enabled: (chartSeries.length > 1)
      },
      yAxis: {
        labels: {
          formatter: function() {
            if(activeMetric == 'revenue') {
              text = '$' + Highcharts.numberFormat(this.value, 0);
            } 
            else if(activeMetric == 'ctr') {
              text = Highcharts.numberFormat(this.value, 0) + '%';
            }
            else {
              if (this.value >= 1000000000) {
                return Highcharts.numberFormat(this.value / 1000000000, 0) + "B";
              } else if (this.value >= 1000000) {
                return Highcharts.numberFormat(this.value / 1000000, 0) + "M";
              } else if (this.value >= 1000) {
                return Highcharts.numberFormat(this.value / 1000, 0) + "K";
              } else if (this.value > 0) {
                return Highcharts.numberFormat(this.value, 0);
              } else {
                return "0";
              }
            }
          }
        }
      },
      tooltip: {
        formatter: function() {
          var text = '', value = '', total = '';

          if(activeMetric == 'revenue') {
            value = '$' + Highcharts.numberFormat(this.y, 0);
            total = '$' + Highcharts.numberFormat(this.total, 0) + ' total';
          }
          else if (activeMetric == 'clicks') {
            value = Highcharts.numberFormat(this.y, 0) + ' ' + activeMetric;
            total = Highcharts.numberFormat(this.total, 0) + ' total ' + activeMetric;
          }
          else if (activeMetric == 'ctr') {
            value = Highcharts.numberFormat(this.y*100, 2) + "% click through";
            total = "";
          }
          else {
            value = Highcharts.numberFormat(this.y, 0) + ' ' + activeMetric;
            total = Highcharts.numberFormat(this.total, 0) + ' total ' + activeMetric;
          }

          text += '<span style="font-size: 14px;">' + Highcharts.dateFormat('%A, %B %e, %Y', this.x) + '</span><br/>';
          text += '<span style="padding: 0; font-weight: 600; color: ' + this.series.color + '">' + this.series.name + '</span>' + ': <strong style="font-weight: 600;">' + value + '</strong><br/>';
          
          if(chartSeries.length > 1) {
            text += '<span style="font-size: 12px; color: #666;">';
            if (this.total > 0 && total) {
              text += '(' + Highcharts.numberFormat(this.percentage, 0) + '% of ' + total + ')';
            }
            else if (total) {
              text += '(' + total + ')';
            }
            text += '</span>';
          }
          return text;
        }
      },
      series: chartSeries
    });
    
    $('#dashboard-stats-chart').removeClass('chart-loading');
  };
  
  Chart.chartError = function() {
    $('#dashboard-stats-chart').removeClass('chart-loading').addClass('chart-error');
  };
  
})(mopub.Chart = mopub.Chart || {}, this.jQuery);

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

