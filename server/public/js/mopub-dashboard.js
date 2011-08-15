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
    
    function getCurrentChartSeriesType() {
        var activeBreakdownsElem = $('#dashboard-stats .stats-breakdown .active');
        if (activeBreakdownsElem.attr('id') == 'stats-breakdown-ctr') return 'line';
        else return 'area';
    }
    
    // Use breakdown to switch charts
    $('.stats-breakdown tr').click(function(e) {
      $('#dashboard-stats-chart').fadeOut(100, function() {
        mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
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
    // $('#dashboard-apps-toggleAllButton')
    //   .button({ 
    //     icons: { primary: "ui-icon-triangle-2-n-s" } 
    //   })
    //   .click(function(e) {
    //     e.preventDefault();
    //   });
    
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
    // $('#dashboard-apps-toggleAllButton').click(function(e) {
    //   e.preventDefault();
    //   var hiddenAppDetails = $('.appData-details .hide').parents('.appData-details');
    //   var shownAppDetails = $('.appData-details .show').parents('.appData-details');
    //   if(hiddenAppDetails.length > 0) {
    //     hiddenAppDetails.each(function() {
    //       $('.appData-details-toggleButton', $(this)).click();
    //     });
    //   }
    //   else {
    //     shownAppDetails.each(function() {
    //       $('.appData-details-toggleButton', $(this)).click();
    //     });
    //   }
    // });

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
    
    // Delete link
    $('#dashboard-delete-link').click(function(e){
      e.preventDefault();
      $('#dashboard-delete-modal').dialog({
        buttons: [
          {
            text: 'Delete',
            click: function() {
              $(this).dialog('close');
              $('#dashboard-deleteForm').submit();
            }
          },
          {
            text: 'Cancel',
            click: function() {
              $(this).dialog('close');
            }
          }
        ]
      });
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
        
        var $full_onlys = $(".full_only");
        var $banner_onlys = $(".banner_only");
        if ($(this).attr("id") == "appForm-adUnitFormat-full-tablet" ||
            $(this).attr("id") == "appForm-adUnitFormat-full"){
                $full_onlys.show();
                $banner_onlys.hide();
            }
        else{
                $full_onlys.hide();
                $banner_onlys.show();
        }    
        
        var $custom_onlys = $(".custom_only");
        if ($(this).attr("id") == "appForm-adUnitFormat-tablet-custom" || $(this).attr("id") == "appForm-adUnitFormat-custom"){
            $custom_onlys.show();
        }
        else{
            $custom_onlys.hide();
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
            $(image).show().css({ opacity: 1 });
            
            var $full_onlys = $(".full_only");
            var $banner_onlys = $(".banner_only");
            if ($(this).attr("id") == "appForm-adUnitFormat-full-tablet" ||
                $(this).attr("id") == "appForm-adUnitFormat-full"){
                    $full_onlys.show();
                    $banner_onlys.hide();
                }
            else{
                    $full_onlys.hide();
                    $banner_onlys.show();
            }    
            
            var $custom_onlys = $(".custom_only");
            if ($(this).attr("id") == "appForm-adUnitFormat-tablet-custom" || $(this).attr("id") == "appForm-adUnitFormat-custom"){
                $custom_onlys.show();
            }
            else{
                $custom_onlys.hide();
            }
            
        }).first().click(); //initialize by activating the first
      });
      
    $("#appForm-adUnitFormat-full-tablet,#appForm-adUnitFormat-full").click(function(e){
        
    })  


      $('#advertisers-testAdServer')
        .button({ icons : {secondary : 'ui-icon-circle-triangle-e'} })
        .click(function(e) {
         e.preventDefault();
         $('#adserverTest').dialog({ 
           buttons: { "Close": function() { $(this).dialog("close"); } }
         });
         $('#adserverTest-iFrame').attr('src',$('#adserverTest-iFrame-src').text());
      });

      //initialize checked elements
      $("#adunit-device_format_phone").parent().children().filter(':checked').click().each(function(){
        var deviceFormat = $(this).val(); //either tablet or phone
        var container = "#adForm-"+deviceFormat+"-container"
        $(container).find('.possible-format').click(); 
      });
  
    // Do Campaign Export Select stuff
    $('#publisher-app-exportSelect')
     .change(function(e) {
        e.preventDefault();
        var val = $(this).val();
        if (val != 'exp') {
            $('#appExportForm')
                .find('#appExportType')
                .val(val)
                .end()
                .submit();
        }
        $(this).selectmenu('index', 0);
    });

    // Hide unneeded li entry
    $('#publisher-app-exportSelect-menu').find('li').first().hide();
  
    // *********************************************************************
    // Begin -- Inventory AJAX
    // *********************************************************************
  
    // Map specific stats from our JSON object to HTML class attributes.
    var jsonKeyToHtmlClassMap = {
        impression_count: "imp",
        request_count: "req",
        click_count: "clk",
        ctr: "ctr",
        fill_rate: "fill",
    };
  
    var adUnitToAppMap = {};
    var statsMap = {};
    var fetchObject;
  
    function isAppId(id) {
      return $("#" + id).hasClass("app-row");
    }
  
    function getAppIdForAdUnitId(adUnitId) {
      return adUnitToAppMap[adUnitId];
    }
    
    function getAllAppIds() {
      return $(".app-row").map(function() { return this.id; });
    }
  
    // Entry point.
    // =====================================================================
  
    if (mopub.isDashboardPage) {
      // setTimeout is a workaround for Chrome: without it, the loading indicator doesn't 
      // disappear until all "onload" AJAX requests are complete.
      setTimeout(initInventoryPage, 0);
    } else {
      mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }
  
    function initInventoryPage() {
      setupAjaxStatusPopup();
      populateGraphWithAccountStats(mopub.accountStats);
    
      var toFetch = [];
    
      // Set up the lists of app/adunit ID lists that we'll need for our AjaxChunkedFetches,
      // as well as the initial statsMap and adUnitToAppMap objects.
      $('.appData').each(function(index, appDataNode) {
        var appRowNode = $(appDataNode).find(".app-row")[0];
      
        var appId = appRowNode.id;
        toFetch.push(appId);
        statsMap[appId] = {};
      
        setAppLoadingSpinnerHidden(appId, false);
      
        var adunitsForApp = $(appDataNode).find(".adunit-row");
        adunitsForApp.each(function(index, adunitNode) {
          var adunitId = adunitNode.id;
        
          toFetch.push(adunitId);
          statsMap[adunitId] = {};
          adUnitToAppMap[adunitId] = appId;
        });
      });
    
      fetchObject = new mopub.Utils.AjaxChunkedFetch({
        days: getNumDaysToFetch() || 14,
        startDate: getStartDate(),
        items: toFetch,
        urlConstructor: inventoryUrlConstructor,
        chunkComplete: inventoryChunkComplete,
        chunkFailure: inventoryChunkFailure,
        fetchComplete: inventoryFetchComplete
      });
      fetchObject.start();
    }
  
    function populateGraphWithAccountStats(stats) {
      var dailyStats = stats["all_stats"]["||"]["daily_stats"];
  
      mopub.dashboardStatsChartData = {
        pointStart: mopub.graphStartDate,
        pointInterval: 86400000,
        requests: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "request_count")}],
        impressions: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "impression_count")}],
        clicks: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "click_count")}],
        users: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "user_count")}]
      };
  
      mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }
  
    function setupAjaxStatusPopup() {
      $("#ajaxRetry").click(function(event) {
        retryFailedFetches();
        $("#ajaxFailure").fadeOut();
        event.preventDefault();
      });

      $("#ajaxDismiss").click(function(event) {
       $("#ajaxFailure").fadeOut(); 
       event.preventDefault();
      });
    }
    
    function retryFailedFetches() {
      // Show the loading spinner for all apps with unfetched ad units.
      var apps = getAllAppIds();
      apps.each(function(index, app) {
        if (!allAdUnitsCompletedForApp(app)) setAppLoadingSpinnerHidden(app, false);
      });
      
      fetchObject.retry();
    }
  
    function getNumDaysToFetch() {
      var daysRadioVal = $("input[name=dashboard-dateOptions-option]:checked").val();
      if (!daysRadioVal || daysRadioVal == "custom") {
        var currentUrl = document.location.href;
        var daysRegex = /r=(\d+)/g;
        var match = daysRegex.exec(currentUrl);
        if (!match || match.length < 2) return null;
        else return match[1];
      }
      else return daysRadioVal;
    }
  
    function getStartDate() {
      var currentUrl = document.location.href;
      var startDateRegex = /s=(\d+-\d+-\d+)/g;
      var match = startDateRegex.exec(currentUrl);
      if (!match || match.length < 2) return null;
      else return match[1];
    }
  
    function inventoryUrlConstructor(chunk, fetchObj) {
      var url = "/campaigns/stats/ajax/?";
      $.each(chunk, function(index, item) {
        if (index == 0) url += "pub=" + item;
        else url += "&pub=" + item;
      });
      if (fetchObj.days) url += "&date_range=" + fetchObj.days;
      if (fetchObj.startDate) url += "&start_date=" + fetchObj.startDate;
      return url;
    }
  
    function formatStatsForDisplay(sumStats) {
      var results = $.extend(true, {}, sumStats);
      results.impression_count = mopub.Utils.formatNumberWithCommas(results.impression_count);
      results.request_count = mopub.Utils.formatNumberWithCommas(results.request_count);
      results.click_count = mopub.Utils.formatNumberWithCommas(results.click_count);
      results.ctr = mopub.Utils.formatNumberAsPercentage(results.ctr);
      results.fill_rate = mopub.Utils.formatNumberAsPercentage(results.fill_rate);
      return results;
    }
  
    function inventoryChunkComplete(data, chunk, fetchObj) {
      var allStats = data["all_stats"];

      for (var key in allStats) {
        var id = key.split("||")[0];
        var sumStats = allStats[key]["sum"];
      
        // Store the stats so that we can build the graph later.
        statsMap[id] = allStats[key];
      
        var formattedStats = formatStatsForDisplay(sumStats);
        $.each(formattedStats, function(key, value) {
          updateStatField(id, key, value);
        });
      }
    
      $.each(chunk, function(index, id) {
        var appId = id;
        
        if (!isAppId(id)) {
          markRowCompleted(id);
          appId = getAppIdForAdUnitId(id);
        }
        
        if (allAdUnitsCompletedForApp(appId)) setAppLoadingSpinnerHidden(appId, true);
      });
    }
  
    function allAdUnitsCompletedForApp(id) {
      return ($("#appData-" + id).find(".incomplete").length == 0);
    }
  
    function markRowCompleted(id) {
      $("#" + id).removeClass("incomplete").addClass("complete");
    }
  
    function updateStatField(id, field, data) {
      if (!id) return;

      var classType = jsonKeyToHtmlClassMap[field];
      if (!classType) return;

      var selector = "#" + id + " ." + classType;
      $(selector).html(data);
    }
  
    function inventoryChunkFailure(chunk, fetchObj) {
      $("#ajaxFailure").show();
      $.each(chunk, function(index, id) {
        var appId = isAppId(id) ? id : getAppIdForAdUnitId(id);
        setAppLoadingSpinnerHidden(appId, true);
      });
    }
  
    function setAppLoadingSpinnerHidden(appId, hidden) {
      var selector = "#" + appId + "-img";
      if (hidden) $(selector).hide();
      else $(selector).show();
    }
  
    function inventoryFetchComplete(fetchObj) {
      prepareGraphFromAppData();
    }
    
    function prepareGraphFromAppData() {
      mopub.dashboardStatsChartData = {
        pointStart: mopub.graphStartDate,
        pointInterval: 86400000,
        requests: getGraphRequestStats(),
        impressions: getGraphImpressionStats(),
        clicks: getGraphClickStats(),
        users: getGraphUserStats()
      };
      
      mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }
    
    function getFetchedAppData() {
      var apps = [];
      
      $.each(statsMap, function(key, value) {
        if (isAppId(key)) {
          var dict = {};
          dict.key = value["name"].replace("||", "");
          dict.stats = value;
          apps.push(dict);
        }
      });
      return apps;
    }
    
    function getGraphRequestStats() {
      var allApps = getFetchedAppData();
      var sortedApps = mopub.Stats.sortStatsObjectsByStat(allApps, "request_count");
      return mopub.Stats.getGraphSummedStatsForStatName("request_count", sortedApps);
    }
    
    function getGraphImpressionStats() {
      var allApps = getFetchedAppData();
      var sortedApps = mopub.Stats.sortStatsObjectsByStat(allApps, "impression_count");
      return mopub.Stats.getGraphSummedStatsForStatName("impression_count", sortedApps);
    }
    
    function getGraphClickStats() {
      var allApps = getFetchedAppData();
      var sortedApps = mopub.Stats.sortStatsObjectsByStat(allApps, "click_count");
      return mopub.Stats.getGraphSummedStatsForStatName("click_count", sortedApps);
    }
    
    function getGraphUserStats() {
      var allApps = getFetchedAppData();
      var sortedApps = mopub.Stats.sortStatsObjectsByStat(allApps, "user_count");
      return mopub.Stats.getGraphSummedStatsForStatName("user_count", sortedApps);
    }
  
    // *********************************************************************
    // End -- Inventory AJAX
    // *********************************************************************
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
