$(document).ready(function() {
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

    function campaignAdgroupFormOnLoad() {
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
                  var fixed_impressions = impressions.toFixed();
                  $('#campaignAdgroupForm input[name="impressions"]').val(fixed_impressions);
                  calculateAndShowBudget();
              }
          } else {
              var budget = $('#campaignAdgroupForm input[name="full_budget"]').val();
              var full_impressions = 1000 * budget / rate;
              if (full_impressions) {
                  var fixed_full_impressions = full_impressions.toFixed();
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

    // Set up the campaign adgroup form for ajax
    $('#campaignAdgroupForm').validate({
        rules: {
            
        },
        submitHandler: function(form) {
            alert('submitting');
            $(form).ajaxSubmit({
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
            });
        }
    })

    $('#campaignAdgroupForm-submit')
        .button({ icons : { secondary : 'ui-icon-circle-triangle-e' } })
        .click(function(e) {
            e.preventDefault();
            $('#campaignAdgroupForm').submit();
        });

    // help links
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

    // date fields
    $('#campaignAdgroupForm input[name="start_date"]').datepicker({ minDate:0 });
    $('#campaignAdgroupForm input[name="end_date"]').datepicker({ minDate:0 });

    // device targeting
    $("#device_targeting_False").click(function(){ 
        $("#target-by-device").slideUp();
    });
    $("#device_targeting_True").click(function() {
        $("#target-by-device").slideDown();
    });
    if($("#device_targeting_True:checked").length === 0) {
        $("#target-by-device").hide();
    }
});