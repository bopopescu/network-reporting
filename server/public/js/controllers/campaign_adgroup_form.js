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

    $('#campaignAdgroupForm-submit')
        .button({ icons : { secondary : 'ui-icon-circle-triangle-e' } })
        .click(function(e) {
            e.preventDefault();
            $('#campaignAdgroupForm').submit();
        });

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


    /* new stuff */
    var validator = $('form#campaign_and_adgroup').validate({
        submitHandler: function(form) {
            $(form).ajaxSubmit({
                data: {ajax: true},
                dataType: 'json',
                success: function(jsonData, statusText, xhr, $form) {
                    if(jsonData.success) {
                        window.location = jsonData.redirect;
                        $('form#campaign_and_adgroup #submit').button({label: 'Success...',
                                                                       disabled: true});
                    }
                    else {
                        validator.showErrors(jsonData.errors);
                        $('form#campaign_and_adgroup #submit').button({label: 'Try Again',
                                                                       disabled: false});
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    $('form#campaign_and_adgroup #submit').button({label: 'Try Again',
                                                                   disabled: false});
                },
                beforeSubmit: function(arr, $form, options) {
                    $('form#campaign_and_adgroup #submit').button({label: 'Submitting...',
                                                                   disabled: true});
                }
            });
        }
    })

    $('form#campaign_and_adgroup #submit')
        .button({ icons : { secondary : 'ui-icon-circle-triangle-e' } })
        .click(function(e) {
            e.preventDefault();
            $('form#campaign_and_adgroup').submit();
        });

    // help links
    // TODO: make sure all of these are necessary, rename?
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

    // date controls
    $('input[type="text"].date').datepicker();

    $('#all-adunits').change(function() {
        // select or deselect all adunits
        $('input[name="site_keys"]').prop('checked', $(this).prop('checked'));
    });

    // device targeting
    $('input[name="device_targeting"]').change(function() {
        if($(this).val() == '0') {
            $('#device_targeting').slideUp();
        }
        else {
            $('#device_targeting').slideDown();
        }
    });
    // update on document ready
    if($('input[name="device_targeting"]').val() == '0') {
        $('#device_targeting').hide();
    }

    // change form based on bid_strategy
    $('select[name="bid_strategy"]').change(function() {
        bid_strategy = $(this).val();
        budget_type_options = $('select[name="budget_type"] option');
        if(bid_strategy == 'cpm') {
            budget_type_options[0].innerHTML = 'impressions/day';
            budget_type_options[1].innerHTML = 'total impressions';
        }
        else {
            budget_type_options[0].innerHTML = 'USD/day';
            budget_type_options[1].innerHTML = 'total USD';
        }
    }).change(); // update on document ready

    var pub_ids = {
        'admob': {'label': 'AdMob Pub ID:', 'placeholder': 'ex: a14cdb1922f35xx'},
        'admob_native': {'label': 'AdMob Pub ID:', 'placeholder': 'ex: a14cdb1922f35xx'},
        'adsense': {'label': 'AdSense ID:', 'placeholder': 'ex: ca-mb-pub-5592664190023789'},
        'brightroll': {'label': 'BrightRoll ID:', 'placeholder': 'ex: 3836789'},
        'chartboost': {'label': 'ChartBoost ID:', 'placeholder': 'ex: 4cf55942bb93162f4500006g'},
        'ejam': {'label': 'eJam Zone ID:', 'placeholder': 'ex: 23710'},
        'greystripe': {'label': 'GreyStripe ID:', 'placeholder': 'ex: 3705265e-1025-4873-9352-7b1e4986xxxx'},
        'inmobi': {'label': 'InMobi ID:', 'placeholder': 'ex: 4028cb962b75ff06012b792fc5fb6789'},
        'jumptap': {'label': 'JumpTap ID:', 'placeholder': 'ex: pa_company_inc_app'},
        'millennial': {'label': 'Millennial ID:', 'placeholder': 'ex: 36789'},
        'millennial_native': {'label': 'Millennial ID:', 'placeholder': 'ex: 36789'},
        'mobfox': {'label': 'MobFox ID:', 'placeholder': 'ex: 008048afe367bf4ce82ae95363c4xxxx'},
    };

    // make necessary changes based on network type
    $('select[name="network_type"]').change(function() {
        network_type = $(this).val();
        $('.network_type_dependant').each(function() {
            $(this).toggle($(this).hasClass(network_type));
        });
        if(network_type in pub_ids) {
            $('label[for$="_pub_id"]').html(pub_ids[network_type].label)
            $('input[name$="_pub_id"]').attr('placeholder', pub_ids[network_type].placeholder)
            $('div.pub_id').show();
        }
        else {
            $('div.pub_id').hide();
        }
    }).change(); // update on document ready

    // make necessary changes based on campaign_type
    $('select[name="campaign_type"]').change(function() {
        campaign_type = $(this).val();
        $('.campaign_type_dependant').each(function() {
            $(this).toggle($(this).hasClass(campaign_type));
        });
        if(campaign_type == 'network') {
            // make necessary changes based on network type
            $('select[name="network_type"]').change();
            // update label and help text for bid_strategy and bid
            $('label[for="id_bid_strategy"]').html('Network Rate');
            // update bid help link
            $('#bid-promo-helpLink').attr('id', 'bid-network-helpLink');
            // update bid_strategy default
            $('select[name="bid_strategy"]').val('cpc');
        }
        else {
            // update label and help text for bid_strategy and bid
            $('label[for="id_bid_strategy"]').html('Rate');
            // update bid_strategy default and trigger update on bid_strategy
            $('select[name="bid_strategy"]').val('cpm').change();
            if(campaign_type == 'promo') {
                // update bid help link
                $('#bid-network-helpLink').attr('id', 'bid-promo-helpLink');
            }
        }
    }).change(); // update on document ready

    // Toggling for advanced options
    $('#toggle_advanced')
        .button('option', {icons: { primary: 'ui-icon-triangle-1-s' }})
        .click(function(e) {
            e.preventDefault();
            var buttonTextElem = $('.ui-button-text', this);
            if ($('fieldset#advanced').is(':hidden')) {
                $('fieldset#advanced').slideDown('fast');
                $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
                $('.ui-button-text', this).text('Hide Advanced Details');
            } else {
                $('fieldset#advanced').slideUp('fast');
                $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
                $('.ui-button-text', this).text('Show Advanced Details');
            }
        }); // TODO: need to update on document ready

    /* GEO TARGETING */
    var geo_s = 'http://ws.geonames.org/searchJSON?';
    var pre = {type: 'country', data: []};
    var city_pre = {type: 'city', data: []};
    //Not being used right now
    //var state_pre = {type: 'state', data: []};
    for (var count = 0; count < countries.length; count++) {
        var dat = countries[count];
        if ($.inArray(dat.code, priors) != -1) {
            pre.data.push(dat);
        }
        if (pre.length == priors.length)
            break;
    }
    //city is ll:ste:name:ccode;
    for (var i in city_priors) {
        if (city_priors.hasOwnProperty(i)) {
            var datas = city_priors[i].split(':');
            var ll = datas[0].split(',');
            var ste = datas[1];
            var name = datas[2];
            var ccode = datas[3];
            city_pre.data.push(
                    { lat: ll[0],
                      lng: ll[1],
                      countryCode: ccode,
                      adminCode1: ste,
                      name: name
                      });
        }
    }
    $('#city_ta').tokenInput(geo_s, {
        country: 'US',
        doImmediate: false,
        hintText: 'Type in a city name',
        queryParam: 'name_startsWith',
        featureClass: 'P',
        prePopulate: city_pre,
        contentType: 'json',
        type: 'city',
        minChars: 3,
        method: 'get'
    });
    //Verify that all cities in city_pre are in the SINGLE country that is pre

    //Need to create data object that is array of dictionary [ {name, id} ]
    $('#geo_pred_ta').tokenInput(null, {
        data: countries,
        hintText: 'Type in a country name',
        formatResult: function( row ) {
            return row.name;
        },
        formatMatch: function( row, i, max ){
            return [row.name, row.code];
        },
        prePopulate: pre
    });
    /* Not doing states atm
    $('#state_ta').tokenInput(geo_s, {
        country: 'US',
        doImmediate: false,
        queryParam: 'name_startsWith',
        featureCode: 'ADM1',
        contentType: 'json',
        prePopulate: state_pre,
        type: 'state',
        minChars: 5,
        method: 'get'
    }); */

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
});
