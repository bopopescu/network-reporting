(function($) {

    function initializeDailyCounts() {
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

            if (data.hasClass('show')) {
                didShowData();
            } else {
                data.hide();
                didHideData();
            }

            button.click(function(e) {
                e.preventDefault();
                if (data.hasClass('show')) {
                    data.slideUp('fast');
                    didHideData();
                } else {
                    data.slideDown('fast');
                    didShowData();
                }
            });
        });
    }


    function manageCreative(action){
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

    function initializeCreativeForm() {
        $('#creativeCreateForm input[name="ad_type"]')
            .click(function(e){
                $('.adTypeDependent',"#creativeCreateForm").hide();
                $('.adTypeDependent.'+$(this).val(),"#creativeCreateForm").show();
            })
            .filter(':checked')
            .click();

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

        $('.creativeEditForm input[name="ad_type"]')
            .click(function(e){
                // gets the form to which this belongs
                var form = $(this).parents('form');
                $('.adTypeDependent',form).hide();
                $('.adTypeDependent.'+$(this).val(),form).show();
            }).filter(':checked').click();


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

        $('#creativeAddForm input[name="creative_type"]')
            .click(function(e) {
                $('#creativeCreate-text_icon').hide();
                $('#creativeCreate-image').hide();
                $('#creativeCreate-html').hide();
                $('#creativeCreate-'+$(this).val()).show();
            })
            .filter(':checked')
            .click(); // make sure we're in sync when the page loads

        $('#creativeAddForm-cancel')
            .button()
            .click(function(e){
                e.preventDefault();
                $('#advertiser-creativeAddForm').slideUp('fast', function() {
                    $('#advertiser-adgroups-addCreativeButton').show();
                });
            });

        // Creative form ajax options
        $('#creativeCreateForm').ajaxForm({
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
                    initializeCreativeForm();
                    window.location.hash = '';
                    window.location.hash = 'advertiser-creativeAddForm';
                    $('#campaignAdgroupForm-submit').button({'label':'Continue','disabled':false});
                }
            },
            error: function(jqXHR, textStatus, errorThrown){

            }
        });


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
    }


    function initializeChart() {
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

        mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
    }


    function fetchInventoryForAdGroup(adgroup_key) {

        // Set up an adunit collection, but remap the url to the
        // adgroup endpoint. this way, we'll only get adunits that
        // belong to this adgroup.
        var adgroup_inventory = new AdUnitCollection();
        adgroup_inventory.adgroup_key = adgroup_key;
        adgroup_inventory.url = function() {
            return '/api/adgroup/'
                + this.adgroup_key
                + '/adunits/';
        };

        // Once the adgroup's adunit inventory has been fetched from
        // the server, render each of the adunits in the appropriate
        // table row. Additionally, fetch the adunit's app from the
        // server and render it too.
        adgroup_inventory.bind('reset', function(adunits){
            adunits.each(function(adunit){
                console.log(adunit);
                var app = new App({ id: adunit.get('app_key') });
                console.log(app);

                //XXX: We need to remap the app's url to only get data
                // for this adgroup

                app.bind('change', function(current_app) {
                    var appView = new AppView({
                        model: app,
                        el: "dashboard-app"
                    });
                    appView.renderInline();
                });

                app.fetch();

                var adunitView = new AdUnitView({
                    model: adunit,
                    el: "dashboard-app"
                });
                adunitView.renderInline();
            });
        });

        adgroup_inventory.fetch();
    }

    var CampaignsController = {
        initializeDirectSold: function(bootstrapping_data) {

            var gtee_adgroups_data = bootstrapping_data.gtee_adgroups_data,
                promo_adgroups_data = bootstrapping_data.promo_adgroups_data,
                backfill_promo_adgroups_data = bootstrapping_data.backfill_promo_adgroups_data,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            // Guaranteed
            var gtee_adgroups = new AdGroups(gtee_adgroups_data);
            var gtee_adgroups_view = new AdGroupsView({
                collection: gtee_adgroups,
                el: '#gtee-adgroups',
                tables: {
                    'High Priority': function(adgroup) {
                        return adgroup.get('level') == 'high';
                    },
                    'Normal Priority': function(adgroup) {
                        return adgroup.get('level') == 'normal';
                    },
                    'Low Priority': function(adgroup) {
                        return adgroup.get('level') == 'low';
                    }
                },
                title: 'Guaranteed Campaigns',
                type: 'gtee'
            });
            gtee_adgroups_view.render();
            gtee_adgroups.each(function(adgroup) { adgroup.fetch({ data: ajax_query_string }); });

            // Promotional
            var promo_adgroups = new AdGroups(promo_adgroups_data);
            var promo_adgroups_view = new AdGroupsView({
                collection: promo_adgroups,
                el: '#promo-adgroups',
                title: 'Promotional Campaigns',
                type: 'promo'
            });
            promo_adgroups_view.render();
            promo_adgroups.each(function(adgroup) { adgroup.fetch({ data: ajax_query_string }); });

            // Backfill Promotional
            var backfill_promo_adgroups = new AdGroups(backfill_promo_adgroups_data);
            var backfill_promo_adgroups_view = new AdGroupsView({
                collection: backfill_promo_adgroups,
                el: '#backfill-promo-adgroups',
                title: 'Backfill Promotional Campaigns',
                type: 'backfill_promo'
            });
            backfill_promo_adgroups_view.render();
            backfill_promo_adgroups.each(function(adgroup) { adgroup.fetch({ data: ajax_query_string }); });

            // TODO: move somewhere else
            $('#campaigns-appFilterOptions').selectmenu({
                style: 'popup',
                maxHeight: 300,
                width:184
            });

            $("#campaigns-filterOptions, #campaigns-appFilterOptions").change(function() {
                gtee_adgroups_view.render();
                promo_adgroups_view.render();
                backfill_promo_adgroups_view.render();
            });

            // Ad Campaign button
            $("#add_campaign_button").button({ icons : { primary : 'ui-icon-circle-plus'} });


            // AdGroups form
            $.each(['pause', 'resume', 'activate', 'archive', 'delete'], function(iter, action) {
                $('#campaignForm-' + action).click(function(e) {
                    e.preventDefault();
                    $('#campaignForm').find("#action").attr("value", action).end().submit();
                });
            });
        },

        initializeAdGroupDetail: function(bootstrapping_data) {
            var kind = bootstrapping_data.kind,
                adgroup_key = bootstrapping_data.adgroup_key;

            initializeCreativeForm();
            initializeChart();
            initializeDailyCounts();
            fetchInventoryForAdGroup(adgroup_key);

            // Set up the click handler for the campaign status menu
            // in the top left of the page.
            $('#campaign-status-options')
                .change(function(e) {
                    var val = $(this).val();
                    $('#fake-campaignForm')
                        .find('#action')
                        .attr('value', val)
                        .end()
                        .submit();
                });

            // Delete redunundant first option
            $('#campaign-status-options-menu')
                .find('li')
                .first()
                .hide();

            // Set up the click handler for the creative status menu
            $.each(['pause', 'resume', 'delete'], function(iter, form_control) {
                $('#creativeManagementForm-' + form_control)
                    .click(function(e){
                        e.preventDefault();
                        manageCreative(form_control);
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
                        buttons: [{
                            text: 'Close',
                            click: function() { $(this).dialog("close"); }
                        }],
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

            $("#add_campaign_button").button({
                icons : { primary : 'ui-icon-circle-plus'}
            });

            $('#advertiser-adgroups-addCreativeButton')
                .button({ icons : { primary : 'ui-icon-circle-plus'} })
                .click(function(e){
                    e.preventDefault();
                        var creative_form = $('#advertiser-creativeAddForm');
                    if (creative_form.is(":hidden")) {
                        $('#advertiser-creativeAddForm').slideDown('fast');
                    } else {
                        $('#advertiser-creativeAddForm').slideUp('fast');
                    }
                });


            $('#advertisers-addCampaign')
                .button({
                    icons : {primary : 'ui-icon-circle-plus'}
                });

            $('#advertisers-adgroups-editAdGroupButton').button({
                icons: { primary: "ui-icon-wrench" }
            });

            $.each(['pause', 'resume', 'activate', 'archive', 'delete'], function(iter, action) {
                $('#campaignForm-' + action)
                    .click(function(e) {
                        e.preventDefault();
                        $('#campaignForm').find("#action").attr("value", action).end().submit();
                    });
            });

            // Delete redunundant first option
            $('#campaign-status-options-menu').find('li').first().hide();

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

            if ($(".creativeData").length === 0 && kind != 'network') {
                $('#chartWrapper').hide();
                $('#advertiser-creativeData').hide();
                $('#advertiser-adgroups-addCreativeButton').click();
            }

        }
    };

    window.CampaignsController = CampaignsController;

})(this.jQuery);
