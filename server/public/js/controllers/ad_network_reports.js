$(function() {


    // Make 'Sort by network', 'Sort by app' sticky
    // NOTE: Would be cleaner if we had the jQuery cookie plugin
    function setCookie(name,value,days) {
        if (days) {
            var date = new Date();
            date.setTime(date.getTime()+(days*24*60*60*1000));
            var expires = "; expires="+date.toGMTString();
        }
        else var expires = "";
        document.cookie = name+"="+value+expires+"; path=/";
    }

    function getCookie(name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        var i;
        for (i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return null;
    }

    function deleteCookie(name) {
        setCookie(name,"",-1);
    }

    //move to a utils package
    // checks if email is valid
    function isValidEmailAddress(emailAddress) {
        var pattern = new RegExp(/^(\s*)(("[\w-+\s]+")|([\w-+]+(?:\.[\w-+]+)*)|("[\w-+\s]+")([\w-+]+(?:\.[\w-+]+)*))(@((?:[\w-+]+\.)*\w[\w-+]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$)|(@\[?((25[0-5]\.|2[0-4][\d]\.|1[\d]{2}\.|[\d]{1,2}\.))((25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\.){2}(25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\]?$)/i);
        return pattern.test(emailAddress);
    };




    var AdNetworkReportsController = {

        initializeAdReportsIndex: function(bootstrapping_data) {
            var networks_data = bootstrapping_data.networks_data,
                apps_data = bootstrapping_data.apps_data,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            // Load account level roll up stats
            var account_roll_up = new AccountRollUp();
            var account_roll_up_view = new AccountRollUpView({
                model: account_roll_up
            });
            account_roll_up.fetch({ data: ajax_query_string });

            // Load graph data
            var daily_stats = new DailyStatsCollection();
            var daily_stats_view = new DailyStatsView({
                collection: daily_stats
            });
            daily_stats.fetch({ data: ajax_query_string });

            // Load rolled up network stats
            var i;
            for (i=0; i < networks_data.length; i++) {
                var network_data = networks_data[i];
                if(network_data['models'].length > 0) {
                    var roll_up = new RollUp({
                        id: network_data['network'],
                        type: 'network'
                    });
                    var roll_up_view = new RollUpView({
                        model: roll_up
                    });
                    roll_up.fetch({ data: ajax_query_string });
                }
            }

            // Load rolled up apps stats
            for (i=0; i < apps_data.length; i++) {
                var app_data = apps_data[i];
                var roll_up = new RollUp({
                    id: app_data['id'],
                    type: 'app'
                });
                var roll_up_view = new RollUpView({
                    model: roll_up
                });
                roll_up.fetch({ data: ajax_query_string });
            }

            // Load stats for app on network
            for (i=0; i < networks_data.length; i++) {
                var network_data = networks_data[i];
                if(network_data['models'].length > 0) {
                    var apps_on_network = new AppOnNetworkCollection(network_data['models']);
                    apps_on_network.each(function(app_on_network) {
                        var app_on_network_view = new AppOnNetworkView({
                            model: app_on_network
                        });
                        app_on_network.fetch({ data: ajax_query_string });
                    });
                }
            }


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

            // taken from mopub-dashboard.js #appEditForm (could be combined)
            $('#networkSettingsForm-submit')
                .button({
                    icons: { secondary: "ui-icon-circle-triangle-e" }
                })
                .click(function(e) {
                    e.preventDefault();
                    $('#networkSettingsForm-loading').show();
                    $('#settings-form-message').hide();

                    // check if all emails are valid
                    var valid = true;
                    var list = $('#network-settingsForm textarea').val().split(',');
                    for (var i = 0; i < list.length; i++) {
                        if (!isValidEmailAddress(list[i])) {
                            valid = false;
                        }
                    }

                    if (valid) {
                        $.ajax({
                            type: 'POST',
                            url: '/ad_network_reports/settings/',
                            data : $('#networkForm').serialize(),
                            success : function(resp) {
                                $('#networkSettingsForm-loading').hide();
                                $('#network-settingsForm').slideUp('fast');
                            },
                            error : function(jqXHR, textStatus, errorThrown) {
                                $('#settings-form-message').html("Couldn't update settings.");
                                $('#settings-form-message').show();
                                $('#networkSettingsForm-loading').hide();
                            }
                        });
                        //$('#networkForm').submit();
                    } else {
                        $('#settings-form-message')
                            .html("Please enter a valid email address or a list of valid email addresses.");
                        $('#settings-form-message').show();
                        $('#networkSettingsForm-loading').hide();
                    }
                });

            $('#networkSettingsForm-cancel')
                .click(function(e) {
                    e.preventDefault();
                    $('#network-settingsForm').slideUp('fast');
                });

            $('#network-settingsButton')
                .button({ icons: { primary: "ui-icon-wrench" } })
                .click(function(e) {
                    e.preventDefault();
                    if ($('#network-settingsForm').is(':visible')) {
                        $('#network-settingsForm').slideUp('fast');
                    } else {
                        $('#network-settingsForm').slideDown('fast');
                    }
                });

            $('#dashboard-sort-network').click(function () {
                deleteCookie('network-reports-tab');
                //$.cookie('network-reports-tab', null);
            });

            $('#dashboard-sort-app').click(function () {
                setCookie('network-reports-tab', '#dashboard-sort-app', 7);
                //$.cookie('network-reports-tab', '#dashboard-sort-app', { expires: 7, path: '/ad_network_reports' });
            });

            if (getCookie('network-reports-tab') == '#dashboard-sort-app') {
                $('#dashboard-sort-app').click();
                $('.apps').addClass('active');
                $('.networks').removeClass('active');
            }

            $('.show-status').click(function () {
                var key = $(this).attr('id');
                var div = $('.' + key);
                div.dialog({
                    buttons: {
                        "Update": function() { $('form.loginCredentials',div).submit(); },
                        "Close": function() { $(this).dialog('close');} }
                });
            });

            $('#dashboard-sort input').click(function() {
                $('.tab-section').hide();
                $('.tab-section.'+$(this).val()).show();
            });

            $('.show-hide').click(function () {
                var key = $(this).attr('id');
                var rows = $('.' + key + '-row');
                var button = $(this).children('span');
                $.each(rows, function (iter, row) {
                    if ($(row).is(":visible")) {
                        $(row).slideUp('fast');
                        $(button).text('Show Apps');
                    } else {
                        $(row).slideDown('fast');
                        $(button).text('Hide Apps');
                    }
                });
            });
        },

        initializeCredentialsPage: function (account_key) {
            $(".loginCredentials").submit(function(event) {
                event.preventDefault();

                // Check if data submitted in the form is valid login
                // information for the ad network
                var data = $(this).serialize();
                var key = $(this).attr('id');
                data += ("&account_key=" + account_key + "&ad_network_name=" + key.substr("form-".length));
                var message = $('.' + key + '-message');
                $(message).removeClass('hidden');
                $(message).html("Verifying login credentials...");
                $.ajax({
                    url: 'https://checklogincredentials.mopub.com',
                    data: data,
                    crossDomain: true,
                    dataType: "jsonp",
                    success: function(valid) {
                        // Upon success notify the user
                        if (valid) {
                            $('.' + key + '-enable').html("Pending");
                            $(message)
                                .html("Check back in a couple minutes to see your ad network revenue report. You will receive an email when it is ready.");
                        } else {
                            $(message).html("Invalid login information.");
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

    window.AdNetworkReportsController = AdNetworkReportsController;
});
