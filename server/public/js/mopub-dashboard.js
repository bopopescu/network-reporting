/*
	MoPub Dashboard JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {
		
		/*---------------------------------------/
		/ Chart
		/---------------------------------------*/
		
		function chartError() {
			$('#dashboard-stats-chart').removeClass('chart-loading').addClass('chart-error');
		}
		
		function setupDashboardStatsChart() {
			// get active metric from breakdown
			var metricElement = $('#dashboard-stats .stats-breakdown .active');
			var metricElementIdComponents = metricElement.attr('id').split('-');
			var activeMetric = metricElementIdComponents[metricElementIdComponents.length - 1];

			// get data
			var data = mopub.dashboardStatsChartData;
			if(typeof data == 'undefined') {
				chartError();
				return;
			};
			
			// set up series
			var colors = ['#0090d9', '#e57300', '#53a600', '#444444'];
			var chartSeries = [];
			var activeData = data[activeMetric];
			if(typeof activeData == 'undefined') {
				chartError();
				return;
			};
			$.each(activeData, function(i, seriesObject) {
				var seriesName, seriesData;
				$.each(seriesObject, function(name, value) {
					seriesName = name;
					seriesData = value;
				});
				chartSeries.push({
					name: seriesName,
					data: seriesData,
					color: colors[i]
				});
			});

			// setup HighCharts chart
			this.trafficChart = new Highcharts.Chart({
				chart: {
					renderTo: 'dashboard-stats-chart',
					defaultSeriesType: 'area'
				},
				plotOptions: {
					series: {
						pointStart: data.pointStart,
						pointInterval: data.pointInterval
					}
				},
				yAxis: {
					labels: {
						formatter: function() {
							var text = Highcharts.numberFormat(this.value, 0);
							if(activeMetric == 'revenue') {
								text = '$' + text;
							}
							return text;
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
						else {
							value = Highcharts.numberFormat(this.y, 0) + ' ' + activeMetric;
							total = Highcharts.numberFormat(this.total, 0) + ' total ' + activeMetric;
						}

						text += '<span style="font-size: 14px;">' + Highcharts.dateFormat('%A, %B %e, %Y', this.x) + '</span><br/>';
						text += '<span style="padding: 0; font-weight: 600; color: ' + this.series.color + '">' + this.series.name + '</span>' + ': <strong style="font-weight: 600;">' + value + '</strong><br/>';
						
						if(chartSeries.length > 1) {
							text += '<span style="font-size: 12px; color: #666;">';
							if(this.total > 0) {
								text += '(' + Highcharts.numberFormat(this.percentage, 0) + '% of ' + total + ')';
							}
							else {
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
		}
		setupDashboardStatsChart();
		
		// Use breakdown to switch charts
		$('.stats-breakdown tr').click(function(e) {
			$('#dashboard-stats-chart').fadeOut('fast', function() {
				setupDashboardStatsChart();
				$(this).fadeIn('fast');
			});
		});
		
		/*---------------------------------------/
		/ UI
		/---------------------------------------*/
		
		// set up dateOptions
		$('#dashboard-dateOptions input').click(function() {
			var option = $(this).val();
			if(option == 'custom') {
				$('#dashboard-dateOptions-custom-modal').dialog({
					width: 570,
					buttons: [
						{
							text: 'Set dates',
							css: { fontWeight: '600' },
							click: function() {
								var from_date=$('#dashboard-dateOptions-custom-from').datepicker("getDate");
								var to_date=$('#dashboard-dateOptions-custom-to').datepicker("getDate");
								var num_days=Math.ceil((to_date.getTime()-from_date.getTime())/(86400000)) + 1;
								
								var from_day=from_date.getDate();
								var from_month=from_date.getMonth()+1;
								var from_year=from_date.getFullYear();
								
								$(this).dialog("close");
								document.location.href = '/inventory/?r='+num_days+'&s='+from_year+"-"+from_month+"-"+from_day;
							}
						},
						{
							text: 'Cancel', 
							click: function() {
								$(this).dialog("close");
							}
						}
					]
				});
			}
			else {
				// Tell server about selected option to get new data
				document.location.href = '/inventory/?r=' + option;
			}
		});
		
		// set up custom dateOptions modal dialog
		$('#dashboard-dateOptions-custom-from').datepicker({
			defaultDate: '-15d',
			maxDate: '0d',
			onSelect: function(selectedDate) {
				var other = $('#dashboard-dateOptions-custom-to');
				var instance = $(this).data("datepicker");
				var date = $.datepicker.parseDate(instance.settings.dateFormat || $.datepicker._defaults.dateFormat, selectedDate, instance.settings);
				other.datepicker('option', 'minDate', date);
			}
		});
		$('#dashboard-dateOptions-custom-to').datepicker({
			defaultDate: '-1d',
			maxDate: '0d',
			onSelect: function(selectedDate) {
				var other = $('#dashboard-dateOptions-custom-from');
				var instance = $(this).data("datepicker");
				var date = $.datepicker.parseDate(instance.settings.dateFormat || $.datepicker._defaults.dateFormat, selectedDate, instance.settings);
				other.datepicker('option', 'maxDate', date);
			}
		});
		
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