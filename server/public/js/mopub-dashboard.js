/*
  MoPub Dashboard JS
*/
// global mopub object
var mopub = mopub || {};
(function($){
  // dom ready
  $(document).ready(function() {
    
    /*----------------------------------------/
    / TODO: Re-organize AJAX stuff            /
    /----------------------------------------*/
    var options = {
      data: { ajax: true },
      dataType: 'json',
      success: function(jsonData, statusText, xhr, $form) {
         $('#appEditForm-loading').hide();

         if (jsonData.success) {
           window.location.reload();
         }
         else {
           $('#appForm-fragment').html(jsonData.html);
           // reimplement the onload event
           appFormOnload();
           window.location.hash = '';
           window.location.hash = 'appForm'; 
        }
      } 
    };
    // Added on a class to differenitate from the the app creation page 
    $('#appForm.appEditForm').ajaxForm(options);

    options = {
      data: { ajax: true },
      dataType: 'json',
      success: function(jsonData, statusText, xhr, $form) {
         $('#adunitForm-loading').hide();
         if (jsonData.success) {
           window.location.reload();
         }
         else {
           $('#adunitForm-fragment').html(jsonData.html);
           // reimplement the onload event
           appFormOnload();
           window.location.hash = '';
           window.location.hash = 'adunitForm';
        }
      } 
    };
    $('#adunitAddForm').ajaxForm(options);


    /*---------------------------------------/
    / Chart
    /---------------------------------------*/
    
    function chartError() {
      $('#dashboard-stats-chart').removeClass('chart-loading').addClass('chart-error');
    }
    
    function setupDashboardStatsChart() {
      // get active metric from breakdown
      var metricElement = $('#dashboard-stats .stats-breakdown .active');
      if (metricElement === null || metricElement.length === 0) {
          return; 
      }
      var metricElementIdComponents = metricElement.attr('id').split('-');
      var activeMetric = metricElementIdComponents[metricElementIdComponents.length - 1];

      // get data
      var data = mopub.dashboardStatsChartData;
      if(typeof data == 'undefined') {
        chartError();
        return;
      }
      
      // set up series
      var colors = ['#0090d9', '#e57300', '#53a600', '#444444'];
      var chartSeries = [];
      var activeData = data[activeMetric];
      if(typeof activeData == 'undefined') {
        chartError();
        return;
      }
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
          defaultSeriesType: 'area',
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
              } else {
                if (this.value > 1000000000) {
                  return Highcharts.numberFormat(this.value / 1000000000, 0) + "B";
                } else if (this.value > 1000000) {
                  return Highcharts.numberFormat(this.value / 1000000, 0) + "M";
                } else if (this.value > 1000) {
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
              value = Highcharts.numberFormat(this.y, 0) + ' ' + activeMetric + " (" + this.point.name + ")";
              total = Highcharts.numberFormat(this.total, 0) + ' total ' + activeMetric;
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
      $('#dashboard-stats-chart').fadeOut(100, function() {
        setupDashboardStatsChart();
        $(this).show();
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
                var location = document.location.href.replace(/\?.*/,'');
                document.location.href = location+'?r='+num_days+'&s='+from_year+"-"+from_month+"-"+from_day;
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
        var location = document.location.href.replace(/\?.*/,'');
        document.location.href = location+'?r=' + option;
      }
    });
    
    // set up stats breakdown dateOptions
    $('#stats-breakdown-dateOptions input').click(function() {
      $('.stats-breakdown-value').hide();
      $('.stats-breakdown-value.'+$(this).val()).show();
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
    $('#dashboard-apps-editAppButton')
      .button({ icons: { primary: "ui-icon-wrench" } })
      .click(function(e) {
        e.preventDefault();
        if ($('#dashboard-appEditForm').is(':visible'))
          $('#dashboard-appEditForm').slideUp('fast');
        else
          $('#dashboard-appEditForm').slideDown('fast');
      });
    $('#dashboard-apps-addAdUnitButton')
      .button({ icons: { primary: "ui-icon-circle-plus" } })
      .click(function(e) {
        e.preventDefault();
        if ($('#dashboard-adunitAddForm').is(':visible'))
          $('#dashboard-adunitAddForm').slideUp('fast');
        else
          $('#dashboard-adunitAddForm').slideDown('fast');
      });
    $('#dashboard-apps-editAdUnitButton')
      .button({ icons: { primary: "ui-icon-wrench" } })
      .click(function(e) {
        e.preventDefault();
        if ($('#dashboard-adunitEditForm').is(':visible'))
          $('#dashboard-adunitEditForm').slideUp('fast');
        else
          $('#dashboard-adunitEditForm').slideDown('fast');
      });
    $('#dashboard-apps-toggleAllButton')
      .button({ 
        icons: { primary: "ui-icon-triangle-2-n-s" } 
      })
      .click(function(e) {
        e.preventDefault();
      });
    
    $('#appEditForm-submit')
      .button({ 
        icons: { secondary: "ui-icon-circle-triangle-e" } 
      })
      .click(function(e) {
        e.preventDefault();
        $('#appEditForm-loading').show();
        $('#appForm').submit();
      });
    $('#appEditForm-cancel')
      .click(function(e) {
        e.preventDefault();
        $('#dashboard-appEditForm').slideUp('fast');
      });
    $('#adunitAddForm-submit')
      .button({ 
        icons: { secondary: "ui-icon-circle-triangle-e" } 
      })
      .click(function(e) {
        e.preventDefault();
        $('#adunitForm-loading').show();
        $('#adunitAddForm').submit();
      });
    $('#adunitAddForm-cancel')
      .click(function(e) {
        e.preventDefault();
        $('#dashboard-adunitAddForm').slideUp('fast', function() {
          $('#dashboard-apps-addAdUnitButton').show();
        });
      });
    $('#adunitEditForm-submit')
      .button({ 
        icons: { secondary: "ui-icon-circle-triangle-e" } 
      })
      .click(function(e) {
        e.preventDefault();
        $('#adunitForm-loading').show();
        $('#adunitAddForm').submit();
      });
    $('#adunitEditForm-cancel')
      .click(function(e) {
        e.preventDefault();
        $('#dashboard-adunitEditForm').slideUp('fast');
    });

    // set up showing/hiding of app details
    $('.appData-details').each(function() {
      var details = $(this);
      var data = $('.appData-details-inner', details);
      var button = $('.appData-details-toggleButton', details);
      
      function getButtonTextElement() {
        var buttonTextElement = $('.ui-button-text', button);
        if(buttonTextElement.length === 0) {buttonTextElement = button;}
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

    /*---------------------------------------/
    / App Details Form
    /---------------------------------------*/
    
    // Submit button
    $('#appForm-submit')
      .button({ 
        icons: { secondary: "ui-icon-circle-triangle-e" } 
      })
      .click(function(e) {
        e.preventDefault();
        $('#appForm').submit();
      });
    
    // Platform-dependent URL/package name switching
    function appFormOnload() {
      $('input[name="app_type"]').click(function(e) {
        $('#appForm .appForm-platformDependent')
          .removeClass('iphone')
          .removeClass('android')
          .removeClass('mweb')
          .addClass($(this).val());
      }).filter(':checked').click(); // make sure we're in sync when the page loads
    }
    appFormOnload();

    $('#appForm-market-search-button')
      .button({ icons: { primary: 'ui-icon-search' }})
      .click(function(e) {
        e.preventDefault();
        $('#searchAppStore-loading').show();
        $('#dashboard-searchAppStore-custom-modal').dialog({
          buttons: [
            {
              text: 'Cancel',
              click: function() {
                $('#searchAppStore-results').html('');
                $(this).dialog('close');
              }
            }
          ]
        });
        var name = $('#appForm input[name="name"]').val();
        $.ajax( {
          url: '/android_market_search/' + name,
          success: loadedArtwork,
          dataType: 'json'
        });
      });

    $('#appForm input[name="app_type"]').click(function(e) {
      $('#appForm .appForm-platformDependent')
        .removeClass('iphone')
        .removeClass('android')
        .addClass($(this).val());
    }).filter(':checked').click();

    $('input[name="name"]').change(function() {
      var name = $.trim($(this).val());
      $('#appForm-adUnitName').val(name + ' banner ad');
    });

    // Search button
    $('#appForm-search-button')
      .button({ icons: { primary: "ui-icon-search" }})
      .click(function(e) {
        e.preventDefault();
        if ($(this).button( "option", "disabled" )) {
          return;
          }

        $('#searchAppStore-loading').show();

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
        script.src = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch?' + 'entity=software&limit=10&callback=loadedArtwork&term='+name;
        var head = document.getElementsByTagName("head")[0];
        (head || document.body).appendChild( script );
      });

    if ($('#appForm-name').val() === '') {
      $('#appForm-search-button').button("disable");
      $('#appForm-search').button("disable");
      $('#appForm-market-search-button').button("disable");
      $('#appForm-market-search').button("disable");
    }

    $('#appForm-name').keyup(function(e) {
      // Show/hide the app search button
      var name = $.trim($(this).val());
      var type = $('input:radio[name="app_type"]:checked').val();

      if (name.length) {
        $('#appForm-search-button').button("enable");
        $('#appForm-market-search-button').button('enable');
      }
      else {
        $('#appForm-search-button').button("disable");
        $('#appForm-market-search-button').button('disable');
      }
      if (e.keyCode == 13) {
        if (type == 'iphone') {
          $('#appForm-search-button').click();
        }
        else if (type == 'android') {
          $('#appForm-market-search-button').click();
        }
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
   
    // Set up device format selection UI
    $("#adunit-device_format_phone").parent().buttonset();
    $('#adunit-device_format_phone').click(function(e){
      $('#adForm-tablet-container').hide();
      $('#adForm-phone-container').show().find('input[type="radio"]')[0].click();
    });
    
    $('#adunit-device_format_tablet').click(function(e){
      $('#adForm-phone-container').hide();
      $('#adForm-tablet-container').show().find('input[type="radio"]')[0].click();
    });
    
    // Set up format selection UI for phone
    $('#adForm-phone-formats').each(function() {
      var container = $(this);
      $('input[type="radio"]', container).click(function(e) {
        var radio = $(this);
        var formatContainer = radio.parents('.adForm-format');
        $('.adForm-format-image').css({ opacity: 0.5 });
        $('.adForm-format-image', formatContainer).css({ opacity: 1 });
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
    
    // /*---------------------------------------/
    // / Stats Geo Breakdown
    // /---------------------------------------*/
    // $('.stats-breakdown.geo tr').click(function(e) {
    //  var row = $(this);
    //  if(!row.hasClass('active')) {
    //      var table = row.parents('table');
    //      $('tr.active', table).removeClass('active');
    //      row.addClass('active');
    //      var $allMaps = $('#allMaps');
    //      $allMaps.removeClass('map-requests');
    //      $allMaps.removeClass('map-impressions');
    //      $allMaps.removeClass('map-clicks');
    //      $allMaps.addClass();
    //      var metricElement = $('#dashboard-geo-stats .stats-breakdown .active');
    //         var metricElementIdComponents = metricElement.attr('id').split('-');
    //         var activeMetric = metricElementIdComponents[metricElementIdComponents.length - 1];
    //         $allMaps.addClass('map-'+activeMetric);
    //  }
    // });
    // 
    // $('#allMaps').addClass('map-requests');
    
    
    // Set up format selection UI for tablet
    $('#adForm-tablet-formats').each(function(){
        var container = $(this);
        //bind radio buttons to images
          $(this).find('input[type="radio"]').click(function(e){
            var index = $(this).parent().index();
            var images = $("#adForm-images-container");
            images.children().hide();
            var image = images.children()[index]
            $(image).show().css({ opacity: 1 });;
        }).first().click(); //initialize by activating the first
      });

      //initialize checked elements
      $("#adunit-device_format_phone").parent().children().filter(':checked').click().each(function(){
        var deviceFormat = $(this).val(); //either tablet or phone
        var container = "#adForm-"+deviceFormat+"-container"
        $(container).find('.possible-format').click(); 
      });
  });
})(this.jQuery);


var artwork_json;

function loadedArtwork(json) {
  if (!$('#dashboard-searchAppStore-custom-modal').dialog("isOpen"))
    return;

  $('#searchAppStore-results').html('');
  $('#searchAppStore-loading').hide();
  $('#dashboard-searchAppStore-custom-modal').dialog("close");

  artwork_json = json;
  var resultCount = json['resultCount'];
  if (resultCount == 0) {
    $('#searchAppStore-results').append("<div class='adForm-appSearch-text' />")
      .append("No results found");
      $('#dashboard-searchAppStore-custom-modal').dialog("open");
      return;
  }
  for (var i=0;i<resultCount;i++) {
    if (i > 10 ) {
        break;
    }
    var app = json['results'][i];
    
    $('#searchAppStore-results').append($("<div class='adForm-appSearch' />")
      .append($("<div class='adForm-appSearch-img' />")
        .append($("<img />")
          .attr("src",app['artworkUrl60'])
          .width(40)
          .height(40)
        )
        .append($("<span />"))
      )
      .append($("<div class='adForm-appSearch-text' />")
        .append($("<span />")
          .append($("<a href=\"#\" onclick=\"selectArtwork("+i+");return false\";>"+app['trackName']+"</a>"))
          .append("<br />"+app['artistName'])
        )
      )
      .append($("<div class='clear' />"))
    );
  }
  
  $('#dashboard-searchAppStore-custom-modal').dialog("open");
}

function selectArtwork(index) {
  $('#searchAppStore-results').html('');
  $('#appForm-icon').html('');
  $('#dashboard-searchAppStore-custom-modal').dialog("close");

  var app = artwork_json.results[index];
  var type = $('input:radio[name="app_type"]:checked').val();

  var form = $('app_form');
  $('#appForm input[name="name"]').val(app['trackName']);
  $('#appForm input[name="description"]').val(app['description']);
  if ( type == 'iphone' )
      $('#appForm input[name="url"]').val(app['trackViewUrl']);
  else if ( type == 'android' )
      $('#appForm input[name="package"]').val(app['trackViewUrl']);
  $('#appForm input[name="img_url"]').val(app['artworkUrl60']);
  
  $('#appForm-icon').append($("<img />")
    .attr("src",app.artworkUrl60)
    .width(40)
    .height(40)
    .append($("<span />"))
  );
}
