$(document).ready(function() {

    // select the appropriate campaign_type from the hash
    if (window.location.hash.substring(1) !== '') {
        $('select[name="campaign_type"]').val(window.location.hash.substring(1));
    }

    var validator = $('form#campaign_and_adgroup').validate({
        errorPlacement: function(error, element) {
            element.closest('li > div').append(error);
        },
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
    });

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
    $('input[type="text"].date').datepicker({minDate: 0});

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

    $('input[name="start_datetime_0"]').change(function(e) {
        e.preventDefault();
        var val = $(this).val();
        if (val != '') {
            $('input[name="start_datetime_1"]').change();
        }
    });

    $('input[name="end_datetime_0"]').change(function(e) {
        e.preventDefault();
        var val = $(this).val();
        if (val != '') {
            $('input[name="end_datetime_1"]').change();
        }
    });

    $('input[name$="_datetime_1"]').change(function(e){
        e.preventDefault();
        var name = $(this).attr('name');
        var val = $(this).val();
        if (name == 'start_datetime_1') {
            if($('input[name="start_datetime_0"]').val() == '') {
                val = '';
            } else {
                val = makeValidTime(val, 12, 0, 'AM');
            }
        }
        else if (name == 'end_datetime_1') {
            if($('input[name="end_datetime_0"]').val() == '') {
                val = '';
            } else {
                val = makeValidTime(val, 11, 59, 'PM');
            }
        }
        $(this).val(val);
    });


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
        'admob_native': 'admob_pub_id',
        'adsense': 'adsense_pub_id',
        'brightroll': 'brightroll_pub_id',
        'ejam': 'ejam_pub_id',
        'inmobi': 'inmobi_pub_id',
        'jumptap': 'jumptap_pub_id',
        'millennial_native': 'millennial_pub_id',
        'mobfox': 'mobfox_pub_id'
    };

    // make necessary changes based on network type
    $('select[name="network_type"]').change(function() {
        var network_type = $(this).val();
        var pub_id = pub_ids[network_type];

        $('.network_type_dependant').each(function() {
            $(this).toggle($(this).hasClass(network_type));
        });

        // for each appropriate input, show either the input or the span and button
        $('ul#apps > li').each(function() {
            var span = $(this).children('div').children('span');
            span.children().hide();
            var input = span.children('input[name$="'+pub_id+'"]');
            var value = input.val();
            $(this).children('div').children('label').attr('for', input.attr('id'));
            if(value) {
                input.siblings('span.pub_id').html(value).show();
                input.siblings('a.pub_id').show();
            }
            else {
                input.show();
            }
            $(this).children('div').children('ul.adunits').children('li').children('span').each(function() {
                var span = $(this);
                span.children().hide();
                var input = span.children('input[name$="'+pub_id+'"]');
                if(input.length) {
                    var value = input.val();
                    if(value) {
                        input.siblings('span.pub_id').html(value).show();
                    }
                    else {
                        input.siblings('span.pub_id').html('Default').show();
                    }
                    input.siblings('a.pub_id').show();
                }
            });
        });

        $('a.pub_id').click(function() {
            var network_type = $('select[name="network_type"]').val();
            var pub_id = pub_ids[network_type];
            $(this).siblings('input[name$="'+pub_id+'"]').show();
            $(this).prev('span').hide();
            $(this).hide();
        });
    }).change(); // update on document ready

    $('button.pub_id').click(function() {
        var network_type = $('select[name="network_type"]').val();
        var pub_id = pub_ids[network_type];

        $(this).siblings('input').hide();
        $(this).prev('span').hide();
        $(this).hide();
        $(this).siblings('input[name$="'+pub_id+'"]').show();
    });

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
        }
        else {
            // update label and help text for bid_strategy and bid
            $('label[for="id_bid_strategy"]').html('Rate');
            if(campaign_type == 'promo') {
                // update bid help link
                $('#bid-network-helpLink').attr('id', 'bid-promo-helpLink');
            }
        }
    }).change(); // update on document ready

    $('select[name="budget_type"]').change(function() {
        budget_type = $(this).val();
        $('.budget_type_dependent').each(function() {
            $(this).toggle($(this).hasClass(budget_type));
        });
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
    var geo_s = 'http://api.geonames.org/searchJSON?username=MoPub&';
    var pre = {type: 'country', data: []};
    var city_pre = {type: 'city', data: []};
    //Not being used right now
    //var state_pre = {type: 'state', data: []};

    window.priors = window.priors || [];

    for(var index in countries) {
        var dat = countries[index];
        if($.inArray(dat.code, window.priors) != -1) {
            pre.data.push(dat);
        }
        if(pre.length == priors.length)
            break;
    }

    window.city_priors = window.city_priors || [];
    //city is ll:ste:name:ccode;
    for(var i in city_priors) {
        if(city_priors.hasOwnProperty(i)) {
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
    $('#campaign_and_adgroup input[name="region_targeting"]').click(function(e) {
        var loc_targ = $(this).val();
        $('.locationDependent', '#campaign_and_adgroup').hide();
        $('.' + loc_targ + '.locationDependent', '#campaign_and_adgroup').show();
        if ($(this).val() == 'all') {
            $('li.token-input-city span.token-input-delete-token').each(function() {
                $(this).click();
            });
        }
    }).filter(':checked').click();

});
