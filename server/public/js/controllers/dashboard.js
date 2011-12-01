/*
 * # MoPub Dashboard
 */

var mopub = mopub || {};
(function($, Backbone, _){

    /*
     * Refactor/remove
     */
    function getCurrentChartSeriesType() {
        var activeBreakdownsElem = $('#dashboard-stats .stats-breakdown .active');
        if (activeBreakdownsElem.attr('id') == 'stats-breakdown-ctr') return 'line';
        else return 'area';
    }

    /*
     * Refactor/remove
     */
    function populateGraphWithAccountStats(stats, start_date) {
        var dailyStats = stats["all_stats"]["||"]["daily_stats"];

        mopub.dashboardStatsChartData = {
            pointStart: start_date,
            pointInterval: 86400000,
            requests: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "request_count")}],
            impressions: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "impression_count")}],
            clicks: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "click_count")}],
            users: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "user_count")}]
        };

        mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }

    /*
     * Fetches all app stats using a list of app keys and renders
     * them into table rows that have already been created in the
     * page. Useful for decreasing page load time along with `fetchAdunitStats`.
     */
    function fetchAppStats (app_keys) {
        _.each(app_keys, function(app_key) {
            var app = new App({id: app_key, stats_endpoint: 'mpx'});
            app.bind('change', function(current_app) {
                var appView = new AppView({ model: current_app, el: '#dashboard-apps' });
                appView.renderInline();
            });
            app.fetch();
        });
    }

    /*
     * Fetches AdUnit stats over ajax and renders them in already existing table rows.
     * This method is useful for decreasing page load time. Uses a parent app's key
     * to bootstrap the fetch.
     */
    function fetchAdunitStats (app_key) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;
        adunits.stats_endpoint = 'mpx';
        // Once the adunits have been fetched from the server,
        // render them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {
            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                var adunitView = new AdUnitView({ model: adunit, el: '#dashboard-apps' });
                adunitView.renderInline();
            });
        });

        adunits.fetch({
            success: function(data){
                // Trigger any event handlers that have been attached to the table.
                // Shouldn't this only trigger for the table that the adunit stats are
                // being placed in?
                $('table').trigger('update');
                $("#" + app_key + "-img").hide();
            }
        });
    }


    /*
     * ## Dashboard Controller
     */
    var DashboardController = {
        initializeIndex: function (bootstrapping_data) {
            //initInventoryPage();
            populateGraphWithAccountStats(bootstrapping_data.account_stats,
                                         bootstrapping_data.start_date);

            fetchAppStats(bootstrapping_data.app_keys);
            _.each(bootstrapping_data.app_keys, function(app_key) {
                fetchAdunitStats(app_key);
            });
        },
        initializeGeo: function (bootstrapping_data) {
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
            // fill this in
        },
        initializeAppDetail: function (bootstrapping_data) {
            // fill this in
        },
        initializeAdUnitDetail: function (bootstrapping_data) {
            // fill this in
        },
        initializeAppCreate: function (bootstrapping_data) {
            // fill this in
        },
        initializeAdUnitCreate: function (bootstrapping_data) {
            // fill this in
        },
    };

    window.DashboardController = DashboardController;


    // BELOW NEEDS TO BE REFACTORED
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
                } else {
                    $('.form-error-text', "#appForm").remove();
                    $.each(jsonData.errors, function (iter, item) {
                        var name = item[0];
                        var error_div = $("<div>").append(item[1]).addClass('form-error-text');

                        $("input[name=" + name + "]", "#appForm")
                            .addClass('error')
                            .parent().append(error_div);

                        $("select[name=" + name + "]", "#appForm")
                            .addClass('error')
                            .parent().append(error_div);


                    });

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
                } else {

                    // reimplement the onload event
                    appFormOnload();
                    setupAdUnitForm();
                    window.location.hash = '';
                    window.location.hash = 'adunitForm';
                }
            }
        };

        $('#adunitAddForm').ajaxForm(options);


        /*---------------------------------------/
          / Chart
          /---------------------------------------*/


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

        $('.appData-id').each(function() {
            var id = $(this)
            var td = id.parents('tr');
            td.hover(
                function() {
                    id.show();
                },
                function() {
                    id.hide();
                });
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

        function setupAdUnitForm() {
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
            //initialize checked elements
            $("#adunit-device_format_phone").parent().children().filter(':checked').click().each(function(){
                var deviceFormat = $(this).val(); //either tablet or phone
                var container = "#adForm-"+deviceFormat+"-container";
                $(container).find('.possible-format').click();
            });
        }
        setupAdUnitForm();

        // /*---------------------------------------/
        // / Stats Geo Breakdown
        // /---------------------------------------*/

        $('#advertisers-testAdServer')
            .button({ icons : {secondary : 'ui-icon-circle-triangle-e'} })
            .click(function(e) {
                e.preventDefault();
                $('#adserverTest').dialog({
                    buttons: { "Close": function() { $(this).dialog("close"); } }
                });
                $('#adserverTest-iFrame').attr('src',$('#adserverTest-iFrame-src').text());
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


        if (mopub.isDashboardPage) {
            // setTimeout is a workaround for Chrome: without it, the loading indicator doesn't
            // disappear until all "onload" AJAX requests are complete.
            //setTimeout(initInventoryPage, 0);
        } else {
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
        }
    });
})(this.jQuery, this.Backbone, this._);


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
    $('#appForm select[name="primary_category"]').val(app['primaryGenreName'].toLowerCase());
    $('#appForm select[name="secondary_category"]').val(app['genres'][1].toLowerCase());

    $('#appForm-icon').append($("<img />")
                              .attr("src",app.artworkUrl60)
                              .width(40)
                              .height(40)
                              .append($("<span />"))
                             );
}
