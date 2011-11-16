/*
 *  MoPub Advertiser JS
 */
var mopub = mopub || {};

(function($){


    var Advertiser = {

        /*
         * Initialize ajax submitting for the credentials form on the
         * credential form page and the index.
         */

        initializeNetworkPage: function () {

        },

        initializeAdReportsIndex: function () {

            $('.addcreds').click(function(e) {
                e.preventDefault();

                var network_name = $(this).attr('href').replace('#', '');

                $("#" + network_name + "-fields").show();

                $("#ad_network_selector").val(network_name);

                $('#credential-form').dialog({
                    buttons: { "Close": function() { $(this).dialog('close');} },
                    width: 500
                });
            });

            $('.app-row').click(function () {
                var app_key = $(this).attr('id');
                var network_rows = $('.for-app-' + app_key);
                $.each(network_rows, function (iter, row) {
                    if ($(row).hasClass('hidden')) {
                        $(row).removeClass('hidden');
                    } else {
                        $(row).addClass('hidden');
                    }
                });
            });
        },

        initializeCredentialsPage: function (management_mode, account_key) {
            $("#loginCredentials").submit(function(event) {
                event.preventDefault();

                // Check if data submitted in the form is valid login
                // information for the ad network
                var data = $(this).serialize();
                data += ("&account_key=" + account_key);
                $.ajax({
                    url: 'http://checklogincredentials.mopub.com',
                    data: data,
                    crossDomain: true,
                    dataType: "jsonp",
                    success: function(valid) {
                        // Upon success update the database
                        if (valid) {
                            if (management_mode) {
                                window.location = "/ad_network_reports/manage/" + account_key;
                            } else {
                                window.location = "/ad_network_reports/";
                            }
                        } else {
                            $("#error").html("Invalid login information.");
                        }
                    }
                });
            });



            // Hides/shows network forms based on which was selected
            // in the dropdown
            $("#ad_network_selector").change(function() {
                var network = $(this).val();
                $('.network_form').each(function () {
                    if ($(this).attr('id') == network + '-fields') {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            }).change();
        }
    };

    window.mopub.Advertiser = Advertiser;


    // dom ready
    $(document).ready(function() {

        //get info from page
        if (typeof creatives=="undefined") {
            creatives = false;
        }

        if ($('#is_admin_input').val() != 'True'){
            $('.admin_only').hide();
        }


        function calculateAndShowBudget() {
            $('#campaignAdgroupForm-budget-display').hide();
            $('#campaignAdgroupForm-budget-display_full').hide();
            if ($('#adgroupForm-bid_strategy-select').val() == 'cpm') {
                var rate = $('#campaignAdgroupForm input[name="bid"]').val();
                if ($("#adgroupForm-budget_type-select").val() == "daily") {
                    var impressions = $('#campaignAdgroupForm input[name="impressions"]').val();
                    var budget = rate * impressions / 1000;
                    if (budget) {
                        var budget_fixed = budget.toFixed(2);
                        $('#campaignAdgroupForm-budget-display').html("("+budget_fixed +" USD / day)");
                        $('#campaignAdgroupForm input[name="budget"]').val(budget);
                        $('#campaignAdgroupForm-budget-display').show();
                    } else {
                        $('#campaignAdgroupForm-budget-display').html(null);
                        $('#campaignAdgroupForm input[name="budget"]').val(null);
                    }
                } else {
                    var impressions = $('#campaignAdgroupForm input[name="full_impressions"]').val();
                    var full_budget = rate*impressions/1000;
                    if (full_budget) {
                        var full_budget_fixed = full_budget.toFixed(2);
                        $('#campaignAdgroupForm-budget-display_full').html("("+full_budget_fixed +" total USD)");
                        $('#campaignAdgroupForm input[name="full_budget"]').val(full_budget);
                        $('#campaignAdgroupForm-budget-display_full').show();
                    } else {
                        $('#campaignAdgroupForm-budget-display_full').html(null);
                        $('#campaignAdgroupForm input[name="full_budget"]').val(null);
                    }
                }
            }
        }

        function campaignAdgroupFormOnLoad(){


            if (window.location.hash.substring(1) !== '') {
                $('#campaign_type_select').val(window.location.hash.substring(1));
            }

            // Select the appropriate form field options based on the type of campaign
            $('#campaign_type_select').change(function(e) {
                var campaign_type = $(this).val();
                window.location.hash = "#" + campaign_type;
                $('.campaignDependent', '#campaignAdgroupForm').hide();
                $('.'+campaign_type+'.campaignDependent', '#campaignAdgroupForm').show();
                $('#campaignAdgroupForm')
                    .find('.campaignDependent').hide().end()
                    .find("."+$(this).val()).show().end();
                if ($(this).val() == "network"){
                    $('#bid_strategy :selected').removeAttr('selected');

                    // make the network bid cpm by default
                    $('option#bid_strategy-cpm').attr('selected','selected');

                    // rename so we dont have duplicates
                    $('#bid-max').attr('name','bid-max');
                    $('#bid-network').attr('name','bid');

                    // rename so we don't have duplicates
                    $('#adgroupForm-bid_strategy-select').attr('name','bid_strategy_std');
                    $('#adgroupForm-bid_strategy-select-network').attr('name','bid_strategy');
                } else {                  // rename so we dont have duplicates
                    $('#bid-network').attr('name','bid-network');
                    $('#bid-max').attr('name','bid');

                    // rename so we don't have duplicates
                    $('#adgroupForm-bid_strategy-select').attr('name','bid_strategy');
                    $('#adgroupForm-bid_strategy-select-network').attr('name','bid_strategy_network');
                }

                if ($(this).val() == 'marketplace') {
                    $("#mpx_message").removeClass('hidden');
                    $('.ui-button-text', "#campaignAdgroupForm-submit").text('Accept New Terms and Continue');
                } else {
                    $("#mpx_message").addClass('hidden');
                  $('.ui-button-text', "#campaignAdgroupForm-submit").text('Continue');
                }
            }).change(); // make sure we're in sync when the page loads

            // Show appropriate options based on what network has been chosen
            // (Network campaigns only)
            $("#network_select").change(function(e) {
              var network = $(this).val();
              $('.networkDependent').hide();
              $('.'+network+'.networkDependent').show();

              if (network == 'admob_native' || network == 'millennial_native') {
                  $('#network_select_sdk_msg').show();
              } else {
                  $('#network_select_sdk_msg').hide();
              }

              if (network == 'iAd') {
                  $('div.adunit-Target.mweb')
                      .hide()
                      .find('input')
                      .removeAttr('checked');
                  $('div.adunit-Target.android')
                      .hide()
                      .find('input')
                      .removeAttr('checked');
              } else {
                  $('div.adunit-Target:hidden').show();
              }
          }).change();

          // Show budget fields when they're needed
          $("#adgroupForm-budget_type-select").change( function(e) {
              var budget_type = $(this).val();
              $('.budgetDependent').hide();
              $('.'+budget_type+'.budgetDependent').show();
              if ($('#adgroupForm-bid_strategy-select').val() == 'cpm') {
                  if (budget_type == "full_campaign") {
                      $('#campaignAdgroupForm-budget-display_full').show();
                  }
                  if (budget_type == "daily"){
                      $('#campaignAdgroupForm-budget-display').show();
                  }
              }
          }).change();

          // Show location-dependent fields when location targeting is turned on
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

          // Toggling for advanced options
          $('#adgroupForm-advanced-toggleButton')
              .button('option', {icons: { primary: 'ui-icon-triangle-1-s' }})
              .click(function(e) {
                  e.preventDefault();
                  var buttonTextElem = $('.ui-button-text', this);
                  if ($('.adgroupForm-advanced').is(':hidden')) {
                      $('.adgroupForm-advanced').slideDown('fast');
                      $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
                      $('.ui-button-text', this).text('Hide Advanced Details');
                  } else {
                      $('.adgroupForm-advanced').slideUp('fast');
                      $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
                      $('.ui-button-text', this).text('Show Advanced Details');
                  }
              });

          // Initialize impression count on form display
          if ($('#adgroupForm-bid_strategy-select').val() == 'cpm') {
              var rate = $('#campaignAdgroupForm input[name="bid"]').val();
              if ($("#adgroupForm-budget_type-select").val() == "daily") {
                  var budget = $('#campaignAdgroupForm input[name="budget"]').val();
                  var impressions = 1000 * budget / rate;
                  if (impressions) {
                      fixed_impressions = impressions.toFixed();
                      $('#campaignAdgroupForm input[name="impressions"]').val(fixed_impressions);
                      calculateAndShowBudget();
                  }
              } else {
                  var budget = $('#campaignAdgroupForm input[name="full_budget"]').val();
                  var full_impressions = 1000 * budget / rate;
                  if (full_impressions) {
                      fixed_full_impressions = full_impressions.toFixed();
                      $('#campaignAdgroupForm input[name="full_impressions"]').val(fixed_full_impressions);
                      calculateAndShowBudget();
                  }
              }
          }

          // Show and update budget controls when needed
          $('#adgroupForm-bid_strategy-select').change(function() {
              if ($(this).val() == 'cpm') {
                  $('.campaignAdgroupForm-budget').hide();
                  $('#campaignAdgroupForm-budget-fullimpressions').show();
                  $('#campaignAdgroupForm-budget-impressions').show();
                  $("#adgroupForm-budget_type-select option[value='full_campaign']").text("total impressions");
                  $("#adgroupForm-budget_type-select option[value='daily']").text("impressions/day");
              } else {
                  $('.campaignAdgroupForm-budget').hide();
                  $('#campaignAdgroupForm-budget-fullbid').show();
                  $('#campaignAdgroupForm-budget-bid').show();
                  $("#adgroupForm-budget_type-select option[value='full_campaign']").text("total USD");
                  $("#adgroupForm-budget_type-select option[value='daily']").text("USD/day");
              }
              calculateAndShowBudget();
          }).change();

          $('#campaignAdgroupForm input[name="impressions"]').keyup(function() {
              calculateAndShowBudget();
          });

          $('#campaignAdgroupForm input[name="full_impressions"]').keyup(function() {
              calculateAndShowBudget();
          });

          $('#bid-max').keyup(function() {
              calculateAndShowBudget();
          });

        $("#terms").dialog({
            autoOpen: false,
            height: 530,
            buttons: {
                "OK": function() {
                    $(this).dialog("close");
                }
            }
        });
        $("#accept_terms").click(function() {
            $("#terms").dialog('open');
        });
      }

      campaignAdgroupFormOnLoad();


      $('#campaignAdgroupForm-submit')
          .button({ icons : {secondary : 'ui-icon-circle-triangle-e'} })
          .click(function(e){
              e.preventDefault();
              if (adgroupFormValidate($('#campaignAdgroupForm'))) {
                  $('#campaignAdgroupForm').submit();
              } else {
                  $('#formError').show();
              }
          });

      $('.adgroupForm-editNetwork-link').click(function(e){
          e.preventDefault();
          var parent = $(this).parents('.adgroupForm-Network');
          parent.find('.adgroupForm-editNetwork').show();
          parent.find('.adgroupForm-showNetwork').hide();
      });

      function adgroupFormValidate(form) {
          var success = true;
          $('#formError').hide();
          $('#fullCampaignError-date').hide();
          $('#fullCampaignError-budget').hide();
          $('#fullCampaignError-name').hide();
          $('#fullCampaignError-bid').hide();

          $('#campaignAdgroupForm input[name="start_date"]').removeClass('form-error');
          $('#campaignAdgroupForm input[name="end_date"]').removeClass('form-error');
          $('#campaignAdgroupForm input[name="full_budget"]').removeClass('form-error');
          $('#campaignAdgroupForm input[name="full_impressions"]').removeClass('form-error');
          $('#campaignAdgroupForm input[name="name"]').removeClass('form-error');
          $('#campaignAdgroupForm input[name="bid"]').removeClass('form-error');

          if ($("#adgroupForm-budget_type-select").val() == "full_campaign" && $("input[name='campaign_type']").filter(':checked').val() == "gtee") {
              if ($("input[name='budget_strategy']").filter(":checked").val() == "evenly") {
                  if ($('#campaignAdgroupForm input[name="start_date"]').val() == '') {
                      $('#campaignAdgroupForm input[name="start_date"]').addClass('form-error');
                      $('#fullCampaignError-date').show();
                      success = false;
                  }

                  if ($('#campaignAdgroupForm input[name="end_date"]').val() == '') {
                      $('#campaignAdgroupForm input[name="end_date"]').addClass('form-error');
                      $('#fullCampaignError-date').show();
                      success = false;
                  }
              }

              if ($('#campaignAdgroupForm input[name="full_budget"]').val() == '') {
                  $('#campaignAdgroupForm input[name="full_budget"]').addClass('form-error');
                  $('#campaignAdgroupForm input[name="full_impressions"]').addClass('form-error');
                  $('#fullCampaignError-budget').show();
                  success = false;
              }

              if ($('#campaignAdgroupForm input[name="name"]').val() == '') {
                  $('#campaignAdgroupForm input[name="name"]').addClass('form-error');
                  $('#fullCampaignError-name').show();
                  success = false;
              }
              if ($('#campaignAdgroupForm input[name="bid"]').val() == '') {
                  $('#campaignAdgroupForm input[name="bid"]').addClass('form-error');
                  $('#fullCampaignError-bid').show();
                  success = false;
              }
          }

          return success;
      }

      // Set up the campaign adgroup form for ajax
      var options = {
          data: { ajax: true },
          dataType: 'json',
          success: function(jsonData, statusText, xhr, $form) {
              $('#campaignAdgroupForm-loading').hide();
              if (jsonData.success){
                  $('#campaignAdgroupForm-success').show(); // show message
                  window.location = jsonData.new_page;
                  $('#campaignAdgroupForm-submit').button({'label':'Success...','disabled':true});
              } else {
                  // $('#campaignAdgroupForm-fragment').html(jsonData.html);
                  // reimplement the onload event
                  campaignAdgroupFormOnLoad();
                  // clear and reset the hash
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
      $('#campaignAdgroupForm').validate(options);
      $('#campaignAdgroupForm').ajaxForm(options);




      $.each(['type', 'priority', 'promo-priority', 'bid', 'keyword'], function(iter, link_type) {
          $('#campaignForm-' + link_type + '-helpLink').click(function(e) {
              e.preventDefault();
              $('#campaignForm-' + link_type + '-helpContent').dialog({
                  buttons: { "Close": function() { $(this).dialog("close"); } }
              });
          });
      });

      $('#campaignForm-customHtml-helpLink').click(function(e) {
          e.preventDefault();
          $('#campaignForm-customHtml-helpContent').dialog({
              buttons: { "Close": function() { $(this).dialog("close"); }},
              width: 700
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

      $.each(['pause', 'resume', 'delete'], function(iter, form_control) {
          $('#creativeManagementForm-' + form_control)
              .click(function(e){
                  e.preventDefault();
                  creativeMange(form_control);
          });
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


      // Creative form ajax options
      options = {
          data: { ajax: true },
          dataType : 'json',
          success: function(jsonData) {
              $('#creativeCreateForm-loading').hide();
              if (jsonData.success) {
                  $('#creativeCreateForm-success').show();
                  window.location.reload();
              } else {
                  $.each(jsonData.errors, function (iter, item) {
                      $('.form-error-text', "#creativeCreateForm").remove();
                      var name = item[0];
                      var error_div = $("<div>").append(item[1]).addClass('form-error-text');

                      $("input[name=" + name + "]", "#creativeCreateForm")
                          .addClass('error')
                          .parent().append(error_div);

                  });
                  // reimplement the onload event
                  creativeCreateFormOnLoad();
                  window.location.hash = '';
                  window.location.hash = 'advertiser-creativeAddForm';
                  $('#campaignAdgroupForm-submit').button({'label':'Continue','disabled':false});
              }
          },
          error: function(jqXHR, textStatus, errorThrown){
              // console.log(errorThrown);
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
                  } else {
                      //$form.find('.creativeEditForm-fragment').html($.decodeHtml(jsonData.html));
                      $('.form-error-text', $form).remove();
                      $.each(jsonData.errors, function (iter, item) {

                          var name = item[0];
                          var error_div = $("<div>").append(item[1]).addClass('form-error-text');

                          $("input[name=" + name + "]", $form)
                              .addClass('error')
                              .parent().append(error_div);

                      });
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
        var width = parseInt($("#"+creative_key+"-preview iframe").attr("width"));
        var height = parseInt($("#"+creative_key+"-preview iframe").attr("height"));
        $("#"+creative_key+"-preview iframe").attr('src', creative_src);
        $("#"+creative_key+"-preview").dialog({
          buttons: [{text: 'Close',click: function() {$(this).dialog("close")}}],
          width: width+100,
          height: height+130
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

        $("#add_campaign_button").button({ icons : { primary : 'ui-icon-circle-plus'} });

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

      function creativeCreateFormOnLoad() {
          $('#creativeCreateForm input[name="ad_type"]')
              .click(function(e){
                  $('.adTypeDependent',"#creativeCreateForm").hide();
                  $('.adTypeDependent.'+$(this).val(),"#creativeCreateForm").show();
              }).filter(':checked').click();

          $('.format-options').change(function(e) {
              e.preventDefault();
              if ($(this).val()=="custom"){
                  $(this).parents("form").find('.customc_only').show();
              } else {
                  $(this).parents("form").find('.customc_only').hide();
              }
              if ($(this).val().search(/full/i) != -1){
                  $(this).parents().find('.full_only').show();
              } else {
                  // $('input[name$=landscape]').removeAttr('checked');
                  $(this).parents().find('.full_only').hide();
              }
          }).change();
      }
      creativeCreateFormOnLoad();

    $('.creativeEditForm input[name="ad_type"]')
      .click(function(e){
        // gets the form to which this belongs
        var form = $(this).parents('form');
        $('.adTypeDependent',form).hide();
        $('.adTypeDependent.'+$(this).val(),form).show();
      }).filter(':checked').click();

    $('#advertisers-addCampaign')
      .button({ icons : {primary : 'ui-icon-circle-plus'} });

    $('#advertisers-adgroups-editAdGroupButton').button({ icons: { primary: "ui-icon-wrench" } });

      $.each(['pause', 'resume', 'activate', 'archive', 'delete'], function(iter, action) {
          $('#campaignForm-' + action)
              .click(function(e) {
                  e.preventDefault();
                  $('#campaignForm').find("#action").attr("value", action).end().submit();
              });
      });


    function refreshAlternatingColor(){
        $('.campaignData').removeClass('campaignData-alt');
        $('table').each(function(){
            $(this).find('.campaignData:visible:odd').addClass('campaignData-alt');
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

    function parseIntFromStatText(statText) {
        var stat = parseInt(statText.replace(/,/g, ''), 10);
        return (isNaN(stat)) ? 0 : stat;
    }

    function parseFloatFromStatText(statText) {
        var stat = parseFloat(statText.replace(/,/g, ''));
        return (isNaN(stat)) ? 0 : stat;
    }

    function setSectionLoadingSpinnerHidden(campaignType, hidden) {
        var classPrefix = campaignType.split('_')[0];
        var selector = '#' + classPrefix + '-loading-img';

        if (hidden) $(selector).hide();
        else $(selector).show();
    }

    function calcAndShowRollupForCampaignType(campaignType, includeInvisibleCampaigns) {
      var req, imp, clk, rev, conv, ctr, fill, ecpm;
      req = imp = clk = rev = conv = ctr = fill = ecpm = 0;

      var classPrefix = campaignType.split('_')[0];

      // Sometimes, we want a rollup to include stats for hidden campaigns. For example, the
      // marketplace campaign is always hidden, but we still want to compute a marketplace rollup.
      // For these cases, we won't include ":visible" as part of our campaign-finding selector.
      var visibleSelector = includeInvisibleCampaigns ? '' : ':visible';

      $('.' + classPrefix + '-req' + visibleSelector).each(function() {
        req += parseIntFromStatText($(this).text());
      });

      $('.' + classPrefix + '-imp' + visibleSelector).each(function() {
        imp += parseIntFromStatText($(this).text());
      });

      $('.' + classPrefix + '-clk' + visibleSelector).each(function() {
        clk += parseIntFromStatText($(this).text());
      });

      // Revenue values may have the "display: none" attribute. When rolling up revenue values,
      // we can't just add up the visible revenue <td>s; we need to filter out those that are
      // a part of visible <tr>s.
      $('.' + classPrefix + '_row' + visibleSelector + ' .' + classPrefix + '-rev').each(
        function() { rev += parseFloatFromStatText($(this).text().replace('$', '')); });

      $('.' + classPrefix + '-conv' + visibleSelector).each(function() {
        conv += parseIntFromStatText($(this).text());
      });

      ctr = (clk === 0 || imp === 0) ? 0 : clk / imp;

      fill = (imp === 0 || req === 0) ? 0 : imp / req;

      ecpm = (rev === 0 || imp === 0) ? 0 : 1000 * (rev / imp);

      $("#" + classPrefix + '-total-req').text(mopub.Utils.formatNumberWithCommas(req));
      $("#" + classPrefix + '-total-imp').text(mopub.Utils.formatNumberWithCommas(imp));
      $("#" + classPrefix + '-total-clk').text(mopub.Utils.formatNumberWithCommas(clk));
      $("#" + classPrefix + '-total-rev').text('$' + mopub.Utils.formatNumberWithCommas(rev.toFixed(2)));
      $("#" + classPrefix + '-total-conv').text(mopub.Utils.formatNumberWithCommas(conv));
      $("#" + classPrefix + '-total-ctr').text(mopub.Utils.formatNumberAsPercentage(ctr));
      $("#" + classPrefix + '-total-fill').text(
        mopub.Utils.formatNumberAsPercentage(fill) + ' (' +
        mopub.Utils.formatNumberWithCommas(req) + ')');
      $("#" + classPrefix + '-total-ecpm').text(
        '$' + mopub.Utils.formatNumberWithCommas(ecpm.toFixed(2)));

      $("#" + classPrefix + '-rollups').show();

      setSectionLoadingSpinnerHidden(campaignType, true);
    }

    function calcRollups() {
        // Don't compute rollups until we've gotten all the information.
        if (!allFetchesCompleted()) return;

        var campaignTypes = [
          CampaignTypeEnum.Guaranteed,
          CampaignTypeEnum.Promotional,
          CampaignTypeEnum.Marketplace,
          CampaignTypeEnum.Network,
          CampaignTypeEnum.Backfill
        ];

        $.each(campaignTypes, function(index, type) {
          var includeInvisibleCampaigns = (type === CampaignTypeEnum.Marketplace);
          calcAndShowRollupForCampaignType(type, includeInvisibleCampaigns);
        });
    }

    // *********************************************************************
    // Begin -- Campaign AJAX
    // *********************************************************************

    var CampaignTypeEnum = {
        Guaranteed: "gtee_row",
        Promotional: "promo_row",
        Network: "network_row",
        Backfill: "bfill_row",
        Marketplace: "marketplace_row",
        BackfillMarketplace: "backfill_marketplace_row",
        All: "campaignData"
    };

    // Map specific stats from our JSON object to HTML class attributes.
    var jsonKeyToHtmlClassMap = {
        status: "status",
        on_schedule: "on_schedule",
        revenue: "rev",
        impression_count: "imp",
        conversion_count: "conv",
        request_count: "req",
        click_count: "clk",
        cpa: "cpa",
        cpc: "cpc",
        cpm: "ecpm",
        ctr: "ctr",
        fill_rate: "fill"
    };

    var campaignsData = {};
    var gteeFetch, promoFetch, networkFetch, bfillFetch, marketplaceFetch, bfMarketplaceFetch;

    // Entry point.
    // =====================================================================

    if (mopub.isNetworksPage) {
      // setTimeout is a workaround for Chrome: without it, the loading indicator doesn't
      // disappear until all "onload" AJAX requests are complete.
      setTimeout(initNetworksPage, 0);
    }

    function initNetworksPage() {
      showOrHideRevenueBreakdown();
      setupAjaxStatusPopup();
      setCampaignFilterOptionsDisabled(true);
      populateCampaignStats();
    }

    function showOrHideRevenueBreakdown() {
      // Hide the revenue breakdown if there are no guaranteed campaigns.
      var guaranteed = getCampaignIdsWithType(CampaignTypeEnum.Guaranteed);
      if (guaranteed.length == 0 && !window.isNetworkPage) $("#stats-breakdown-revenue").hide();
      else $("#stats-breakdown-revenue").show();
    }

    function getCampaignIdsWithType(type) {
      return $("." + type).map(function() { return $(this).attr("id"); });
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
      var fetches = [gteeFetch, promoFetch, networkFetch, bfillFetch, marketplaceFetch,
        bfMarketplaceFetch];

      $.each(fetches, function(index, fetch) {
        if (fetch.hasFailed) {
          setSectionLoadingSpinnerHidden(fetch.campaignType, false);
          fetch.start();
        }
      });
    }

    function setCampaignFilterOptionsDisabled(disabled) {
      $("#campaigns-filterOptions").buttonset({"disabled": disabled});
    }

    function populateStatsBreakdownsWithData(data) {
      var allStats = data["all_stats"]["||"];
      var dailyStats = allStats["daily_stats"];
      var yesterday;
      var all;

      var today = formatStatsForDisplay(dailyStats[dailyStats.length - 1]);
      if (dailyStats.length >= 2){
        yesterday = formatStatsForDisplay(dailyStats[dailyStats.length - 2]);
      }

      all = formatStatsForDisplay(allStats.sum);

      $("#stats-breakdown-impressions .today .inner").html(today.impression_count);
      $("#stats-breakdown-revenue .today .inner").html(today.revenue);//"$" + today.revenue.toFixed(2));
      $("#stats-breakdown-clicks .today .inner").html(today.click_count);
      $("#stats-breakdown-ctr .today .inner").html(today.ctr);

      if (yesterday != null) {
        $("#stats-breakdown-impressions .yesterday .inner").html(yesterday.impression_count);
        $("#stats-breakdown-revenue .yesterday .inner").html(yesterday.revenue);//"$" + yesterday.revenue.toFixed(2));
        $("#stats-breakdown-clicks .yesterday .inner").html(yesterday.click_count);
        $("#stats-breakdown-ctr .yesterday .inner").html(yesterday.ctr);
      }

      $("#stats-breakdown-impressions .all .inner").html(all.impression_count);
      $("#stats-breakdown-revenue .all .inner").html(all.revenue);//"$" + all.revenue.toFixed(2));
      $("#stats-breakdown-clicks .all .inner").html(all.click_count);
      $("#stats-breakdown-ctr .all .inner").html(all.ctr);
    }

    function formatStatsForDisplay(sumStats) {
      var results = $.extend(true, {}, sumStats);
      results.impression_count = mopub.Utils.formatNumberWithCommas(results.impression_count);
      results.conversion_count = mopub.Utils.formatNumberWithCommas(results.conversion_count) +
        " (" + mopub.Utils.formatNumberAsPercentage(results.conv_rate) + ")";
      results.request_count = mopub.Utils.formatNumberWithCommas(results.request_count);
      results.click_count = mopub.Utils.formatNumberWithCommas(results.click_count);
      results.cpa = "$" + results.cpa.toFixed(2);
      results.cpc = "$" + results.cpc.toFixed(2);
      results.cpm = "$" + results.cpm.toFixed(2);
      results.revenue = "$" + results.revenue.toFixed(2);
      results.ctr = mopub.Utils.formatNumberAsPercentage(results.ctr);
      results.fill_rate = mopub.Utils.formatNumberAsPercentage(results.fill_rate);

      var onScheduleHtml = "";
      if (results.status == "Running") {
        if (results.on_schedule == "on pace") {
          onScheduleHtml = '<span class="osi-success"> On pace ' +
            '<a href="#" id="campaign-osi-success-helpLink" class="whatsthis">' +
            '<div class="whatsthis-icon"></div></a></span>';
        } else if (results.on_schedule == "behind") {
          onScheduleHtml = '<span class="osi-failure""> Behind ' +
            '<a href="#" id="campaign-osi-failure-helpLink" class="whatsthis">' +
            '<div class="whatsthis-icon"></div></a></span>';
        }
      }
      results.on_schedule = onScheduleHtml;

      return results;
    }

    function populateGraphWithAccountStats(stats) {
      var dailyStats = stats["all_stats"]["||"]["daily_stats"];

      mopub.dashboardStatsChartData = {
        pointStart: mopub.graphStartDate,
        pointInterval: 86400000,
        impressions: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "impression_count")}],
        revenue: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "revenue")}],
        clicks: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "click_count")}],
        ctr: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "ctr")}]
      };

      mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }

    function populateCampaignStats() {
      var allCampaignIds = getCampaignIdsWithType(CampaignTypeEnum.All);
      $.each(allCampaignIds, function(index, id) {
        campaignsData[id] = {};
      });

      var argsDict = {
        days: getNumDaysToFetch() || 14,
        startDate: getStartDate()
      };

      var guaranteedIds = getCampaignIdsWithType(CampaignTypeEnum.Guaranteed);
      var promotionalIds = getCampaignIdsWithType(CampaignTypeEnum.Promotional);
      var networkIds = getCampaignIdsWithType(CampaignTypeEnum.Network);
      var backfillIds = getCampaignIdsWithType(CampaignTypeEnum.Backfill);
      var marketplaceIds = getCampaignIdsWithType(CampaignTypeEnum.Marketplace);
      var bfMarketplaceIds = getCampaignIdsWithType(CampaignTypeEnum.BackfillMarketplace);

      gteeFetch = createCampaignStatsFetchObject(guaranteedIds, argsDict);
      gteeFetch.campaignType = CampaignTypeEnum.Guaranteed;

      promoFetch = createCampaignStatsFetchObject(promotionalIds, argsDict);
      promoFetch.campaignType = CampaignTypeEnum.Promotional;

      networkFetch = createCampaignStatsFetchObject(networkIds, argsDict);
      networkFetch.campaignType = CampaignTypeEnum.Network;

      bfillFetch = createCampaignStatsFetchObject(backfillIds, argsDict);
      bfillFetch.campaignType = CampaignTypeEnum.Backfill;

      marketplaceFetch = createCampaignStatsFetchObject(marketplaceIds, argsDict);
      marketplaceFetch.campaignType = CampaignTypeEnum.Marketplace;

      bfMarketplaceFetch = createCampaignStatsFetchObject(bfMarketplaceIds, argsDict);
      bfMarketplaceFetch.campaignType = CampaignTypeEnum.BackfillMarketplace;

      var fetches = [gteeFetch, promoFetch, networkFetch, bfillFetch, marketplaceFetch,
        bfMarketplaceFetch];
      $.each(fetches, function(index, fetch) {
        setSectionLoadingSpinnerHidden(fetch.campaignType, false);
        fetch.start();
      });
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

    function createCampaignStatsFetchObject(campaigns, argsDict) {
      var options = {
        items: campaigns,
        urlConstructor: campaignStatsUrlConstructor,
        chunkComplete: campaignStatsChunkComplete,
        chunkFailure: campaignStatsChunkFailure,
        fetchComplete: campaignStatsFetchComplete
      };
      $.extend(true, options, argsDict);
      return new mopub.Utils.AjaxChunkedFetch(options);
    }

    function campaignStatsUrlConstructor(chunk, fetchObj) {
      var url = "/campaigns/stats/ajax/?";
      $.each(chunk, function(index, item) {
        if (index == 0) url += "adv=" + item;
        else url += "&adv=" + item;
      });
      if (fetchObj.days) url += "&date_range=" + fetchObj.days;
      if (fetchObj.startDate) url += "&start_date=" + fetchObj.startDate;
      return url;
    }

    function campaignStatsChunkComplete(data, chunk, fetchObj) {
      var allStats = data["all_stats"];

      if(!mopub.accountStats) {
        mopub.accountStats = {
          "all_stats": {
            "||": {
              "daily_stats": []
            }
          }
        }
      }

      for (var key in allStats) {
        var campaignId = key.split("||")[1];
        var sumStats = allStats[key]["sum"];

        var index;
        for(index in allStats[key]["daily_stats"]) {
          if(mopub.accountStats['all_stats']['||']['daily_stats'].length <= index) {
            mopub.accountStats['all_stats']['||']['daily_stats'][index] = allStats[key]["daily_stats"][index];
          }
          else {
            for(stat in allStats[key]["daily_stats"][index]) {
              mopub.accountStats['all_stats']['||']['daily_stats'][index][stat] += allStats[key]["daily_stats"][index][stat];
            }
          }
        }

        // Store the stats so that we can build the graph later.
        campaignsData[campaignId] = allStats[key];

        var formattedStats = formatStatsForDisplay(sumStats);
        $.each(formattedStats, function(key, value) {
          updateCampaignField(campaignId, key, value);
        });

        updateCampaignStatus(campaignId, formattedStats.status);
        updateHelpLinks();
      }

      showCampaignsMatchingStatusFilter();
    }

    function updateCampaignField(campaign, field, data) {
      if (!campaign) return;

      var classType = jsonKeyToHtmlClassMap[field];
      if (!classType) return;

      var selector = "#" + campaign + " ." + classType;
      $(selector).html(data);
    };

    function updateCampaignStatus(campaignId, status) {
      // Set campaign status to "Running", "Paused", etc. via class attribute.
      var selector = "#" + campaignId;
      $(selector).removeClass("incomplete")
        .addClass("complete")
        .addClass("campaign-status-" + status);
    }

    function updateHelpLinks() {
      $('.complete .ecpm-helpLink').html("What's this?");

      $('.whatsthis').click(function(e) {
        e.preventDefault();
        $('#'+$(this).attr('id').replace('helpLink', 'helpContent')).dialog({
          buttons: { "Close": function() { $(this).dialog('close');} }
        });
      });
    }

    function campaignStatsChunkFailure(chunk, fetchObj) {
      $("#ajaxFailure").show();
      setSectionLoadingSpinnerHidden(fetchObj.campaignType, true);
    }

    function campaignStatsFetchComplete(fetchObj) {
      var campaignType = fetchObj.campaignType;
      var includeInvisibleCampaigns = (campaignType === CampaignTypeEnum.Marketplace);
      calcAndShowRollupForCampaignType(campaignType, includeInvisibleCampaigns);
      if (allFetchesCompleted()) onCampaignsFullyUpdated();
    }

    function allFetchesCompleted() {
      return (gteeFetch && gteeFetch.isComplete && promoFetch && promoFetch.isComplete &&
        networkFetch && networkFetch.isComplete && bfillFetch && bfillFetch.isComplete &&
        marketplaceFetch && marketplaceFetch.isComplete &&
        bfMarketplaceFetch && bfMarketplaceFetch.isComplete);
    }

    function onCampaignsFullyUpdated() {
      setCampaignFilterOptionsDisabled(false);
      calcRollups();
      sumAccountStats();
      populateStatsBreakdownsWithData(mopub.accountStats);
      populateGraphWithAccountStats(mopub.accountStats);
      prepareGraphFromCampaignData();
    }

    function sumAccountStats() {
      mopub.accountStats["all_stats"]["||"]["sum"] = {
        "fill_rate": 0, "impression_user_count": 0, "user_count": 0, "request_user_count": 0, "ctr": 0, "revenue": 0.0, "cpa": 0, "impression_count": 0, "conversion_count": 0, "reqs": [], "conv_rate": 0, "cpc": 0, "request_count": 0, "click_count": 0, "date": "2011-11-03 00:00:00", "click_user_count": 0, "offline": false, "cpm": 0
      }
      var index;
      var stat;
      for(index in mopub.accountStats["all_stats"]["||"]["daily_stats"]) {
        for(stat in mopub.accountStats["all_stats"]["||"]["sum"]) {
          mopub.accountStats["all_stats"]["||"]["sum"][stat] += mopub.accountStats["all_stats"]["||"]["daily_stats"][index][stat];
        }
      }

    }

    function prepareGraphFromCampaignData() {
      mopub.dashboardStatsChartData = {
        pointStart: mopub.graphStartDate,
        pointInterval: 86400000,
        impressions: getGraphImpressionStats(),
        revenue: getGraphRevenueStats(),
        clicks: getGraphClickStats(),
        ctr: getGraphCtrStats()
      };

      mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }

    // Helpers for creating the stat objects needed in graph construction.
    // =====================================================================

    function getFetchedCampaignsWithType(type) {
      var matchingCampaignIds = getCampaignIdsWithType(type);

      var campaigns = [];
      $.each(campaignsData, function(key, value) {
        if ($.inArray(key, matchingCampaignIds) != -1) {
          var dict = {};
          dict.key = value["name"].replace("||", "");
          dict.stats = value;
          campaigns.push(dict);
        }
      });
      return campaigns;
    }

    function getGraphImpressionStats() {
      var allCampaigns = getFetchedCampaignsWithType(CampaignTypeEnum.All);
      var sortedCampaigns = mopub.Stats.sortStatsObjectsByStat(allCampaigns, "impression_count");
      return mopub.Stats.getGraphSummedStatsForStatName("impression_count", sortedCampaigns);
    }

    function getGraphRevenueStats() {
      // We only care about guaranteed campaigns when graphing revenue.
      var allGuaranteed = getFetchedCampaignsWithType(CampaignTypeEnum.Guaranteed);
      var sortedGuaranteed = mopub.Stats.sortStatsObjectsByStat(allGuaranteed, "revenue");
      return mopub.Stats.getGraphSummedStatsForStatName("revenue", sortedGuaranteed);
    }

    function getGraphClickStats() {
      var allCampaigns = getFetchedCampaignsWithType(CampaignTypeEnum.All);
      var sortedCampaigns = mopub.Stats.sortStatsObjectsByStat(allCampaigns, "impression_count");
      return mopub.Stats.getGraphSummedStatsForStatName("click_count", sortedCampaigns);
    }

    function getGraphCtrStats() {
      var allCampaigns = getFetchedCampaignsWithType(CampaignTypeEnum.All);
      var sortedCampaigns = mopub.Stats.sortStatsObjectsByStat(allCampaigns, "impression_count");

      var result = mopub.Stats.getGraphCtrStats(sortedCampaigns);
      // Append stats for MoPub-optimized CTR.
      var accountDailyStats = mopub.accountStats["all_stats"]["||"]["daily_stats"];
      var mopubOptimized = {
        "MoPub Optimized": mopub.Stats.statArrayFromDailyStats(accountDailyStats, "ctr"),
      };
      result.push(mopubOptimized);
      return result;
    }

    // *********************************************************************
    // End -- Campaign AJAX
    // *********************************************************************

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

    function showCampaignsMatchingStatusFilter(){
        var statusFilter = $("#campaigns-filterOptions").find(':checked').val();
        if (!statusFilter) return;
        var appFilter = $('#campaigns-appFilterOptions').val();
        window.location.hash = "status:" + statusFilter + "&app:" + appFilter;
        // Hide all the campaigns, then show the ones that pass the filters
        $('.campaignData').hide();
        $('.'+appFilter).filter('.'+statusFilter).show();

        hideEmptyDirects();
        refreshAlternatingColor();
        calcRollups();
    }

    // We filter whenever the user changes the filtering options
    $("#campaigns-filterOptions, #campaigns-appFilterOptions").change(function(){
        showCampaignsMatchingStatusFilter();
    });
    showCampaignsMatchingStatusFilter();

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
                    $options.slideDown('fast').removeClass('hidden');
                    $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
                    $('.ui-button-text', this).text('Less Options');
                } else {
                    $options.slideUp('fast').addClass('hidden');
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

     // Set up device targeting
     $("#device_targeting_False").click(function(){
       $("#target-by-device").slideUp();
     });
     $("#device_targeting_True").click(function(){
       $("#target-by-device").slideDown();
     });
     if ($("#device_targeting_True:checked").length === 0) {
       $("#target-by-device").hide();
     }

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
            if (hiddenAppDetails.length > 0) {
                hiddenAppDetails.each(function() {
                    $('.appData-details-toggleButton', $(this)).click();
                });
            } else {
                shownAppDetails.each(function() {
                    $('.appData-details-toggleButton', $(this)).click();
                });
            }
        });

        // Do Campaign Export Select stuff
        $('#advertiser-adgroups-exportSelect')
            .change(function(e) {
                e.preventDefault();
                var val = $(this).val();
                if (val != 'exp') {
                    $('#campaignExportForm')
                        .find('#campaignExportType')
                        .val(val)
                        .end()
                        .submit();
                }
                $(this).selectmenu('index', 0);
            });

        // Hide unneeded li entry
        $('#advertiser-adgroups-exportSelect-menu').find('li').first().hide();

        // For campaigns/create //

        if ($("#campaignForm-details") != []){
            // Only execute this if we are on the new campaigns form
            var preselected_tag = window.location.hash.substr(1);
            $("#advertiser-CampaignType-"+preselected_tag).click();
        }

    function makeValidTime(timeStr, defHour, defMin, defAmPm) {
        // Checks to see if a timeStr is valid, returns valid form
        // AM/PM (and variants) are optional.

        var timePat = /^(\d{1,2}):(\d{2})(\s?(AM|am|PM|pm|aM|pM|Pm|Am))?$/;

        if (defMin < 10) {
            defMin = '0' + defMin;
        }
        var matchArray = timeStr.match(timePat);
        if (matchArray == null) {
            return defHour + ':' + defMin + ' ' + defAmPm;
        }

        hour = matchArray[1];
        minute = matchArray[2];
        ampm = matchArray[4];

        // Handle military time stuff
        if (hour >= 12 && hour <= 23) {
            hour = hour - 12;
            // 12:00 AM to 12:00 PM
            // 12:00    to 12:00 PM
            //
            // 15:00 AM to 3:00 PM
            // 15:00 PM to 3:00 PM
            // 15:00    to 3:00 PM
            if (hour == 0) {
                hour = 12;
                if (ampm === undefined) {
                    ampm = 'PM';
                }
            }
            else {
                ampm = 'PM';
            }
        }

        if (hour == 0) {
            ampm = 'AM';
            hour = 12;
        }
        // Set invalid times to 0 minutes and 12 hours and default to AM
        if (minute < 0 || minute > 59) {
            minute = defMin;
        }
        if (hour < 0 || hour > 23) {
            hour = defHour;
        }
        if (ampm === undefined) {
            ampm = defAmPm;
        }

        else {
            ampm = ampm.toUpperCase();
        }
        return hour + ':' + minute + ' ' + ampm ;
    }

    $('#start-date').change(function(e) {
        e.preventDefault();
        var val = $(this).val();
        if (val != '') {
            $('#start-time').change();
        }
    });

    $('#stop-date').change(function(e) {
        e.preventDefault();
        var val = $(this).val();
        if (val != '') {
            $('#stop-time').change();
        }
    });

    $('.input-text-time').change(function(e){
        e.preventDefault();
        var id = $(this).attr('id');
        var val = $(this).val();
        if (id == 'start-time') {
            if($('#start-date').val()=='') {
                val = '';
            } else {
                val = makeValidTime(val, 12, 0, 'AM');
            }
        }
        else if (id == 'stop-time') {
            if($('#stop-date').val()=='') {
                val = '';
            } else {
                val = makeValidTime(val, 11, 59, 'PM');
            }
        }
        $(this).val(val);
    });


        $("#stats-breakdown-revenue").show();

        if (mopub.isNetworkPage) {
            $("#stats-breakdown-revenue").click(function() {
                $("#dashboard-stats-chart").hide().attr('style', 'display:none;').remove();
                $("#revenue-chart").show();
            });

            $.each(['impressions', 'clicks', 'ctr'], function (iter, item) {
                $("#stats-breakdown-" + item).click(function() {
                    $("#revenue-chart").hide();
                    $("#dashboard-stats-chart").show();
                });
            });
        }
    }); // End document31 onready
 })(this.jQuery);
