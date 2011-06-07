/*
  MoPub Advertiser JS
*/

// We list standard globals for jslint */
/*globals $, log, window */

// We also list some globals that we have defined. TODO: clean this up
/*globals calculateAndShowBudget, Highcharts, creatives*/

// global mopub object
var mopub = mopub || {};

(function($){
  // dom ready
  $(document).ready(function() {
    
    //get info from page
  if (typeof creatives=="undefined") {
    creatives = false;
    }

  function campaignAdgroupFormOnLoad(){
    $('#campaignAdgroupForm input[name="campaign_type"]').click(function(e) {
      var campaign_type = $(this).val();
      $('.campaignDependent', '#campaignAdgroupForm').hide();
      $('.'+campaign_type+'.campaignDependent', '#campaignAdgroupForm').show();
      $('#campaignAdgroupForm')
          .find('.campaignDependent').hide().end()
          .find("."+$(this).val()).show().end();
      if ($(this).val() == "network"){
        $('#bid_strategy :selected').removeAttr('selected');
        $('option#bid_strategy-cpm').attr('selected','selected'); // make the network bid cpm by default
        $('#bid-max').attr('name','bid-max'); // rename so we dont have duplicates
        $('#bid-network').attr('name','bid');
        
        $('#adgroupForm-bid_strategy-select').attr('name','bid_strategy_std'); // rename so we don't have duplicates
        $('#adgroupForm-bid_strategy-select-network').attr('name','bid_strategy');
      }
      else{
        $('#bid-network').attr('name','bid-network'); // rename so we dont have duplicates
        $('#bid-max').attr('name','bid');
        
        $('#adgroupForm-bid_strategy-select').attr('name','bid_strategy'); // rename so we don't have duplicates
        $('#adgroupForm-bid_strategy-select-network').attr('name','bid_strategy_network');
      }    
    }).filter(':checked').click(); // make sure we're in sync when the page loads

    $("#network_select").change( function(e) {
            var network = $(this).val();
            $('.networkDependent').hide();
            $('.'+network+'.networkDependent').show();
            if (network == 'iAd') {
                $('div.adunit-Target.mweb')
                .hide()
                .find('input')
                .removeAttr('checked');
                $('div.adunit-Target.android')
                .hide()
                .find('input')
                .removeAttr('checked');
            }
            else {
                $('div.adunit-Target:hidden').show();
            }
            }).change();

    $('#campaignAdgroupForm input[name="location-targeting"]').click(function(e) {
            var loc_targ = $(this).val();
            $('.locationDependent', '#campaignAdgroupForm').hide();
            $('.' + loc_targ + '.locationDependent', '#campaignAdgroupForm').show();
            if ($(this).val() == 'all') {
                $('li.token-input-city span.token-input-delete-token').each(function() {
                    $(this).click();
                    });
            }
            }).filter(':checked').click();
    
    $('#adgroupForm-advanced-toggleButton')
      .button('option', {icons: { primary: 'ui-icon-triangle-1-s' }})
      .click(function(e) {
        e.preventDefault();
        var buttonTextElem = $('.ui-button-text', this);
        if ($('.adgroupForm-advanced').is(':hidden')) {
          $('.adgroupForm-advanced').slideDown('fast');
          $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
          $('.ui-button-text', this).text('Hide Advanced Details');
        }
        else {
          $('.adgroupForm-advanced').slideUp('fast');
          $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
          $('.ui-button-text', this).text('Show Advanced Details');
        }
      });
    $('#adgroupForm-bid_strategy-select')
      .change(function() {
        if ($(this).val() == 'cpm') {
          $('.campaignAdgroupForm-budget').hide();
          $('#campaignAdgroupForm-budget-impressions').show();
        }
        else {
          $('.campaignAdgroupForm-budget').hide();
          $('#campaignAdgroupForm-budget-bid').show();
        }
        calculateAndShowBudget();
      });
    $('#campaignAdgroupForm input[name="impressions"]')
      .keyup(function() {
        calculateAndShowBudget();        
      });
    $('#bid-max')
      .keyup(function() {
        calculateAndShowBudget();        
      });
    // Initialize impression count on form display
    if ($('#adgroupForm-bid_strategy-select').val() == 'cpm') {
      var rate = $('#campaignAdgroupForm input[name="bid"]').val();
      var budget = $('#campaignAdgroupForm input[name="budget"]').val();
      var impressions = 1000 * budget / rate;
      if (impressions) {
        $('#campaignAdgroupForm input[name="impressions"]').val(impressions);
        calculateAndShowBudget();
      }
    }
  }
   
  campaignAdgroupFormOnLoad(); 
  
  function calculateAndShowBudget() {
    $('#campaignAdgroupForm-budget-display').hide();
    if ($('#adgroupForm-bid_strategy-select').val() == 'cpm') {
      var rate = $('#campaignAdgroupForm input[name="bid"]').val();
      var impressions = $('#campaignAdgroupForm input[name="impressions"]').val();
      var budget = rate * impressions / 1000;
      if (budget) {
        var budget_fixed = budget.toFixed(2);
        $('#campaignAdgroupForm-budget-display').html("("+budget_fixed +" USD / day)");
        $('#campaignAdgroupForm input[name="budget"]').val(budget);
        $('#campaignAdgroupForm-budget-display').show();
      }
    }
  }
  
  var options = { 
    data: { ajax: true },
    dataType: 'json',
    success: function(jsonData, statusText, xhr, $form) {
	console.log(jsonData);
      $('#campaignAdgroupForm-loading').hide();
      if (jsonData.success){
        $('#campaignAdgroupForm-success').show(); // show message
        window.location = jsonData.new_page;
        $('#campaignAdgroupForm-submit').button({'label':'Success...','disabled':true});
      }
      else{
        $('#campaignAdgroupForm-fragment').html(jsonData.html);
        // reimplement the onload event
        campaignAdgroupFormOnLoad();
        // clear and reset the hash
        window.location.hash = '';
        window.location.hash = 'adgroupEditForm';
        $('#campaignAdgroupForm-submit').button({'label':'Continue','disabled':false});
        
      }
    },
    error: function(jqXHR, textStatus, errorThrown){
        $('#campaignAdgroupForm-submit').button({'label':'Try Again','disabled':false});
    },
    // NOTE: I am not sure this will play nicely with jquery validation
    beforeSubmit: function(arr, $form, options){
        $('#campaignAdgroupForm-submit').button({'label':'Submitting...','disabled':true});
    } 
  };
  $('#campaignAdgroupForm').ajaxForm(options);

  // set up "Help" links
  $('#campaignForm-type-helpLink').click(function(e) {
    e.preventDefault();
    $('#campaignForm-type-helpContent').dialog({ 
      buttons: { "Close": function() { $(this).dialog("close"); } }
    });
  });
  $('#campaignForm-priority-helpLink').click(function(e) {
      e.preventDefault();
      $('#campaignForm-priority-helpContent').dialog({
          buttons: { "Close": function() { $(this).dialog('close'); }}
      });
  });

  $('#campaignForm-promo-priority-helpLink').click(function(e) {
      e.preventDefault();
      $('#campaignForm-promo-priority-helpContent').dialog({
          buttons: { "Close": function() { $(this).dialog('close'); }}
      });
  });

  $('#campaignForm-customHtml-helpLink').click(function(e) {
    e.preventDefault();
    $('#campaignForm-customHtml-helpContent').dialog({ 
      buttons: { "Close": function() { $(this).dialog("close"); } }
    });
  });

  $('#advertisers-testAdServer')
    .button({ icons : {secondary : 'ui-icon-circle-triangle-e'} })
    .click(function(e) {
     e.preventDefault();
     $('#adserverTest').dialog({ 
       buttons: { "Close": function() { $(this).dialog("close"); } }
     });
     $('#adserverTest-iFrame').attr('src',$('#adserverTest-iFrame-src').text());
  });
  
  $('#campaignForm-bid-helpLink').click(function(e) {
    e.preventDefault();
    $('#campaignForm-bid-helpContent').dialog({ 
      buttons: { "Close": function() { $(this).dialog("close"); } }
    });
  });
  $('#campaignForm-keyword-helpLink').click(function(e) {
    e.preventDefault();
    $('#campaignForm-keyword-helpContent').dialog({ 
      buttons: { "Close": function() { $(this).dialog("close"); } }
    });
  });
  
  
  
  $('#campaignAdgroupForm input[name="start_date"]').datepicker({ minDate:0 });
  $('#campaignAdgroupForm input[name="end_date"]').datepicker({ minDate:0 });

  function creativeMange(action){
    $('#creativeManagementForm-action').val(action);
    var $form = $('#creativeManagementForm');
    $form.find('input[name="key"]').remove();
    $('#advertiser-creativeData').find('input[name="creativeManagementForm-key"]:checked')
      .each(function(i){
        $(this).val(); // key
        $('<input></input>').attr('name','key').attr('type','hidden')
          .val($(this).val())
          .appendTo($form);
      });
    $form.submit();
  }  
    
   $('#creativeManagementForm-pause')
    .click(function(e){
      e.preventDefault();
      creativeMange('pause');
    });
    
   $('#creativeManagementForm-resume')
    .click(function(e){
      e.preventDefault();
      creativeMange('resume');
    });

   $('#creativeManagementForm-delete')
    .click(function(e){
      e.preventDefault();
      creativeMange('delete');
    });

   $('.creativeManagementForm-key')
    .change(function(e){
      $('#creativeManagementForm input[name="key"]').remove(); // remove all keys
      $('.creativeManagementForm-key:checked')
        .each(function(i){
          $(this).val(); // key
        });
      var $form = $('#creativeManagementForm');
    });
    
   options = { 
   data: { ajax: true },
   dataType : 'json',
    success: function(jsonData) { 
      $('#creativeCreateForm-loading').hide();
        if (jsonData.success) {
          $('#creativeCreateForm-success').show(); // show message
          $('#advertiser-creativeAddForm')
            .slideUp('slow', function() {
              $('#advertiser-adgroups-addCreativeButton').show();
              $('#creativeCreateForm-success').hide(); // hide message
              $('#creativeCreateForm').resetForm();
              window.location.reload();
            });
        }
        else{
          $('#creativeAddForm-fragment').html(jsonData.html);
          // reimplement the onload event
          $('#creativeCreateForm input[name="ad_type"]')
            .click(function(e){
              $('#creativeCreateForm')
                .find('.adTypeDependent').hide().end()
                .find('.'+$(this).val()).show().end();
              }).filter(':checked').click();
          window.location.hash = ''; 
          window.location.hash = 'advertiser-creativeAddForm'; 
        }
      },
      error: function(jqXHR, textStatus, errorThrown){
        log(errorThrown);
      }
    };
    $('#creativeCreateForm').ajaxForm(options);
                 
    $('.creativeEditForm').each(function(i){
      var $this = $(this);
      var options = {
        data: { ajax : true },
        dataType: 'json',
        success: function(jsonData, statusText, xhr, $form){
          $form.find('.creativeEditForm-loading').hide();
          if (jsonData.success){
            $form.find('.creativeCreateForm-success').show();
            $form.parent();
            $form.find('.creativeCreateForm-success').hide();
            window.location.reload();
          }
          else{
            $form.find('.creativeEditForm-fragment').html(jsonData.html);
            // re-implement onload
            $('.creativeEditForm input[name="ad_type"]')
              .click(function(e){
                $(this).parents('form') // gets the form to which this belongs
                  .find('.adTypeDependent').hide().end()
                  .find('.'+$(this).val()).show().end();
              }).filter(':checked').click();
            window.location.hash = '';    
            window.location.hash = $form.prev("a").attr('name');
          }
        }
      };
      $(this).ajaxForm(options);
    });

    $('.creativeEditForm-submit')
      .button()
      .click(function(e) {
        e.preventDefault();
        $(this).parents('form').find('.creativeEditForm-loading').show();
        $(this).parents('form').submit();
    });
    
    $('.creativeEditForm-cancel')
      .button()
      .click(function(e) {
        e.preventDefault();
        $(this).parents('.advertiser-creativeEditForm')
          .dialog('close');
    });

    $('.advertiser-inLineCreativePreview')
      .button({ icons : { primary : 'ui-icon-search' }})
      .click(function(e){
        e.preventDefault();
        var creative_key = $(this).attr("id");
        var creative_src = $('#'+creative_key+'-preview-src').val();
        $("#"+creative_key+"-preview iframe").attr('src', creative_src);
        $("#"+creative_key+"-preview").dialog({
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

    $('.advertiser-inLineCreativeToggle')
      .button({ icons : { primary : 'ui-icon-wrench' }})
      .click(function(e){
        e.preventDefault();
        var creative_key = $(this).attr("id");
        var creative_form = $("#"+creative_key+"-edit");
        creative_form.dialog({width:1000});
      });
    
    $('#advertiser-adgroups-addCreativeButton')
      .button({ icons : { primary : 'ui-icon-circle-plus'} })
      .click(function(e){
          e.preventDefault();
          var creative_form = $('#advertiser-creativeAddForm');
          if (creative_form.is(":hidden")) {
            $('#advertiser-creativeAddForm').slideDown('fast');
          }
          else {
            $('#advertiser-creativeAddForm').slideUp('fast');
          }
        });
        
    if (!creatives) {
      $('#chartWrapper').hide();
      $('#advertiser-creativeData').hide();
      $('#advertiser-adgroups-addCreativeButton').click();
    }

    $('#creativeCreateForm input[name="ad_type"]')
      .click(function(e){
        $('.adTypeDependent',"#creativeCreateForm").hide();
        $('.adTypeDependent.'+$(this).val(),"#creativeCreateForm").show();
      }).filter(':checked').click();


    $('.creativeEditForm input[name="ad_type"]')
      .click(function(e){
        // gets the form to which this belongs
        var form = $(this).parents('form');
        $('.adTypeDependent',form).hide();
        $('.adTypeDependent.'+$(this).val(),form).show();
      }).filter(':checked').click();

    
    $('#campaignAdgroupForm-submit')
      .button({ icons : {secondary : 'ui-icon-circle-triangle-e'} })
      .click(function(e){
        e.preventDefault();
        $('#campaignAdgroupForm').submit();
      });
      
    ////////////////////////////////////
    //////////  /campaigns/ ////////////
    ////////////////////////////////////
    
    $('#advertisers-addCampaign')
      .button({ icons : {primary : 'ui-icon-circle-plus'} });
    
    $('#advertisers-adgroups-editAdGroupButton').button({ icons: { primary: "ui-icon-wrench" } });

    $('#campaignForm-pause')
      .click(function(e) {
        e.preventDefault();
        $('#campaignForm').find("#action").attr("value","pause").end().submit();
    });

    $('#campaignForm-resume')
      .click(function(e) {
        e.preventDefault();
        $('#campaignForm').find("#action").attr("value","resume").end().submit();
    });

    $('#campaignForm-delete')
      .click(function(e) {
        e.preventDefault();
        $('#campaignForm').find("#action").attr("value","delete").end().submit();
    });
    
    
                
    ///// Filter Campaigns by status and targeted apps /////    
    
    
    function refreshAlternatingColor(){
        $('.campaignData').removeClass('campaignData-alt');
        $('table').each(function(){
            $(this).find('.campaignData:visible:odd').addClass('campaignData-alt');
        });
    }
    
    function addPlaceholder(){
        // Placeholders start out hidden
        $('.campaignData-placeholder').hide();
        $('table').each(function(){
            // Show them where there is nothing else
            var visible = $(this).find('.campaignData:visible');
            if (visible.length === 0){
                var placeholder = $(this).find('.campaignData-placeholder');
                placeholder.show();
            }
        });
    }

    function get_radio_label(value) {
        return "campaigns-filterOptions-option-"+value.split("campaign-status-")[1];
    }

    function checkFilterHash() {
        var hash = window.location.hash.split('&');
        var statusFilter, appFilter;
        if (hash[0].indexOf('status') != -1) {
            statusFilter = hash[0];
            appFilter = hash[1];
        }
        else {
            statusFilter = hash[1];
            appFilter = hash[0];
        }
        try {
            //assuming hash values are correct here
            statusFilter = statusFilter.split('status:')[1];
            appFilter = appFilter.split('app:')[1];
        }
        catch(err) {
            // Someone fucked with the hash values, just ignore it
            return;
        }
        var statusRadio = $('input[value="'+statusFilter+'"]');
        var statusLabel = $('label[for="'+get_radio_label(statusFilter)+'"]');
        var appOpt = $('option[value="'+appFilter+'"]');
        //Use the right value
        appOpt.attr('selected', 'selected');
        //Do the right value
        statusRadio.click();
        //Show the right value
        statusLabel.click();


    }
    checkFilterHash();
    function addCommas(nStr)
    {
        nStr += '';
        x = nStr.split('.');
        x1 = x[0];
        x2 = x.length > 1 ? '.' + x[1] : '';
        var rgx = /(\d+)(\d{3})/;
        while (rgx.test(x1)) {
            x1 = x1.replace(rgx, '$1' + ',' + '$2');
        }
        return x1 + x2;
    }
    
    function formatPercentage(number){
      // We round to two decimal places
      return (number*100).toFixed(2) + '%';
    }
    
    function calcRollups() {
        //rollup gtee's 
        if ($('.gtee-placeholder').is(":visible")) {
            $('#gtee-rollups').hide();
        }
        else {
            $('#gtee-rollups').show();
            var gtee_imp, gtee_clk, gtee_rev;
            gtee_imp = gtee_clk = gtee_rev = 0;
            $('.gtee-imp:visible').each(function() {
                    gtee_imp += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $('.gtee-clk:visible').each(function() {
                    gtee_clk += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            //Yuuuckkkkk
            $('tr.gtee_row:visible td.gtee-rev').each(function() {
                    gtee_rev += parseInt($(this).text().replace(/,/g,''), 10);
                    });

            $('#gtee-total-imp').text(addCommas(gtee_imp));
            $('#gtee-total-clk').text(addCommas(gtee_clk));
            $('#gtee-total-rev').text('$'+addCommas(Math.round(gtee_rev*100)/100));
            var gtee_ctr;
            if (gtee_clk === 0) {
                gtee_ctr = formatPercentage(0);
            }
            else {
                gtee_ctr = formatPercentage(gtee_clk/gtee_imp, 2);
            }
            $('#gtee-total-ctr').text(gtee_ctr);
        }

        
        if ($('.bfill-placeholder').is(":visible")) {
            $('#bfill-rollups').hide();
        }
        else {
            $('#bfill-rollups').show();
            var bfill_imp, bfill_clk, bfill_conv;
            bfill_imp = bfill_clk = bfill_conv = 0;
            $('.bfill-imp:visible').each(function() {
                    bfill_imp += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $('.bfill-clk:visible').each(function() {
                    bfill_clk += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $('.bfill-conv:visible').each(function() {
                    bfill_conv += parseInt($(this).text().replace(/,/g,''), 10);
                    });

            $("#bfill-total-imp").text(addCommas(bfill_imp));
            $("#bfill-total-clk").text(addCommas(bfill_clk));
            $("#bfill-total-conv").text(addCommas(bfill_conv));
            var bfill_ctr;
            if (bfill_clk === 0) {
                bfill_ctr = formatPercentage(0);
            }
            else {
                bfill_ctr = formatPercentage(bfill_clk/bfill_imp);
            }
            $("#bfill-total-ctr").text(bfill_ctr);
        }
        
        if ($('.promo-placeholder').is(":visible")) {
            $('#promo-rollups').hide();
        }
        else {
            $('#promo-rollups').show();
            var promo_imp, promo_clk, promo_conv;
            promo_imp = promo_clk = promo_conv = 0;
            $('.promo-imp:visible').each(function() {
                    promo_imp += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $('.promo-clk:visible').each(function() {
                    promo_clk += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $('.promo-conv:visible').each(function() {
                    promo_conv += parseInt($(this).text().replace(/,/g,''), 10);
                    });

            $("#promo-total-imp").text(addCommas(promo_imp));
            $("#promo-total-clk").text(addCommas(promo_clk));
            $("#promo-total-conv").text(addCommas(promo_conv));
            var promo_ctr;
            if (promo_clk === 0) {
                promo_ctr = formatPercentage(0);
            }
            else {
                promo_ctr = formatPercentage(promo_clk/promo_imp);
            }
            $("#promo-total-ctr").text(promo_ctr);
        }



        if ($('.network-placeholder').is(":visible")) {
            $('#network-rollups').hide();
        }
        else {
            $('#network-rollups').show();
            var net_imp, net_clk, net_req;
            net_imp = net_clk = net_req = 0;
            $('.network-imp').each(function() {
                    net_imp += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $('.network-clk').each(function() {
                    net_clk += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $('.network-req').each(function() {
                    net_req += parseInt($(this).text().replace(/,/g,''), 10);
                    });
            $("#network-total-imp").text(addCommas(net_imp));
            $("#network-total-clk").text(addCommas(net_clk));
            var net_ctr;
            if (net_clk === 0) {
                net_ctr = formatPercentage(0);
            }
            else {
                net_ctr = formatPercentage(net_clk/net_imp);
            }
            $("#network-total-ctr").text(net_ctr);
            var net_fill;
            if (net_imp === 0) {
                net_fill = formatPercentage(0);
            }
            else {
                net_fill = formatPercentage(net_imp/net_req);
            }
            $('#network-total-fill').text(net_fill + ' (' + addCommas(net_req) + ')');
        }
    }

    
    function hideEmptyDirects(){
        var somethingToDisplay = false;
         $.each([$('#campaignDataTable-direct-high'),
                 $('#campaignDataTable-direct-low'),
                 $('#campaignDataTable-direct-normal')],function(){
                     $(this).show();
                 });
        
        function hideIfEmpty(){
             var visible = $(this).find('.campaignData:visible');
             if (visible.length === 0){
                 $(this).hide();
             }else{
                 somethingToDisplay = true;
             }
        }
        $.each([$('#campaignDataTable-direct-high'),
                 $('#campaignDataTable-direct-low')],
                 hideIfEmpty);
        if(somethingToDisplay){
             $.each([$('#campaignDataTable-direct-normal')],
                         hideIfEmpty);
        }        
    }

    function applyFilters(){
        var statusFilter = $("#campaigns-filterOptions").find(':checked').val();
        var appFilter = $('#campaigns-appFilterOptions').val();
        window.location.hash = "status:" + statusFilter + "&app:" + appFilter;
        // Hide all the campaigns, then show the ones that pass the filters
        $('.campaignData').hide();
        $('.'+appFilter).filter('.'+statusFilter).show();
        
        hideEmptyDirects();
        addPlaceholder();
        refreshAlternatingColor();
        calcRollups();
    }
    
    // We filter whenever the user changes the filtering options
    $("#campaigns-filterOptions, #campaigns-appFilterOptions").change(function(){
        applyFilters();
    });
    applyFilters();

    //jQuery magic last
    $('#campaigns-appFilterOptions').selectmenu({
        style: 'popup',
        maxHeight: 300,
        width:184
    });
                
    ////////////////////////////////////////////
    //////////  /campaigns/adgroup/ ////////////
    ////////////////////////////////////////////
    
    $('#creativeCreateForm-submit')
      .button({ 
        icons: { secondary: "ui-icon-circle-triangle-e" } 
      })
      .click(function(e) {
        e.preventDefault();
        $('#creativeCreateForm-loading').show();
        $('#creativeCreateForm').submit();
    });
    
    $('#creativeCreateForm-cancel')
      .button()
      .click(function(e) {
          e.preventDefault();
        $('#advertiser-creativeAddForm').slideUp('fast', function() {
          $('#advertiser-adgroups-addCreativeButton').show();
        });
      });
    
    $('.creativeFormAdvancedToggleButton')
      .button('option', {icons: { primary: 'ui-icon-triangle-1-s' }})
      .click(function(e) {
        e.preventDefault();
        var $options = $(this).parents('form').find('.creativeForm-advanced-options');
        if ($options.is(':hidden')) {
          $options.slideDown('fast');
          $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
          $('.ui-button-text', this).text('Less Options');
        }
        else {
          $options.slideUp('fast');
          $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
          $('.ui-button-text', this).text('More Options');
        }
      });
    
    $('.creativeAddForm-url-helpLink').click(function(e) {
      e.preventDefault();
      $('#creativeAddForm-url-helpContent').dialog({ 
        buttons: { "Close": function() { $(this).dialog("close"); } }
      });
    }); 
    
    $('.format-options').change(function(e) {
        e.preventDefault();
          if ($(this).val()=="custom"){
              $(this).parents("form").find('.customc_only').show();
              }
          else{
              $(this).parents("form").find('.customc_only').hide();
          }
          if ($(this).val().search(/full/i) != -1){
              $(this).parents().find('.full_only').show();
          }
          else{
             // $('input[name$=landscape]').removeAttr('checked');
              $(this).parents().find('.full_only').hide()
          }
      }).change();

    $('#creativeAddForm input[name="creative_type"]').click(function(e) {
      $('#creativeCreate-text_icon').hide();
      $('#creativeCreate-image').hide();
      $('#creativeCreate-html').hide();
      $('#creativeCreate-'+$(this).val()).show();
    }).filter(':checked').click(); // make sure we're in sync when the page loads

    $('#creativeAddForm-cancel')
      .button()
      .click(function(e){
        e.preventDefault();
        $('#advertiser-creativeAddForm').slideUp('fast', function() {
          $('#advertiser-adgroups-addCreativeButton').show();
        });
      });

    //////// Set up the status buttons at the top ///////
    $('#campaign-status-options')
      .change(function(e) {
          var val = $(this).val();  
          $('#fake-campaignForm').find('#action').attr('value', val).end().submit();
          });
          
     // Delete redunundant first option
     $('#campaign-status-options-menu').find('li').first().hide();
    
    /*---------------------------------------/
    / Chart
    /---------------------------------------*/
    
    function chartError() {
      $('#dashboard-stats-chart').removeClass('chart-loading').addClass('chart-error');
    }
    
    function setupDashboardStatsChart(seriesType) {
      // get active metric from breakdown
      var metricElement = $('#dashboard-stats .stats-breakdown .active');
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
          
          if (seriesType == 'line'){
             if (seriesName == 'Mopub Optimized'){
              seriesLineWidth = 4;
            } else{
              seriesLineWidth = 2;
            }
          }
          else{
            seriesLineWidth = 3;
          }
          
        });
        chartSeries.push({
          name: seriesName,
          data: seriesData,
          color: colors[i],
          lineWidth: seriesLineWidth,
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
            
            if((chartSeries.length > 1) && (total != "")) {
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
    if ($('#dashboard-stats').length){
      setupDashboardStatsChart('area');
    }

    // Use breakdown to switch charts
    $('.stats-breakdown tr:not(#stats-breakdown-ctr)').click(function(e) {
      $('#dashboard-stats-chart').fadeOut('fast', function() {
        setupDashboardStatsChart('area');
        $(this).fadeIn('fast');
      });
    });
    
    // Remove the standard click handler and replace it
    $('#stats-breakdown-ctr').click(function(){
        $('#dashboard-stats-chart').fadeOut('fast', function(){
            setupDashboardStatsChart('line');
            $(this).fadeIn('fast');
        });
    });
    
    /*---------------------------------------/
    / UI
    /---------------------------------------*/
    
    // set up dateOptions
    $('#dashboard-dateOptions input').click(function() {
      var option = $(this).val();
      var hash = document.location.hash;
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
                var location = document.location.href.replace(hash, '').replace(/\?.*/,'');
                document.location.href = location+'?r='+num_days+'&s='+from_year+"-"+from_month+"-"+from_day + hash;
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
        var location = document.location.href.replace(hash,'').replace(/\?.*/,'');
        document.location.href = location+'?r=' + option + hash;
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
    $('#dashboard-apps-editAppButton').button({ icons: { primary: "ui-icon-wrench" } });
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
        if(buttonTextElement.length === 0) { 
            buttonTextElement = button;
        }
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
