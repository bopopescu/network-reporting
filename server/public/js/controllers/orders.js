(function ($, mopub) {
    "use strict";

    /*
     * # Utility functions for rendering models.
     * REFACTOR: move to views/inventory.js
     */
    function renderOrder(order, render_line_items) {

        if (typeof render_line_items === 'undefined') {
            render_line_items = true;
        }

        var order_view = new OrderView({
            model: order,
            el: 'inventory_table'
        });
        order_view.renderInline();

        if (render_line_items) {
            var line_items = new LineItemCollection(order.get('adgroups'));
            line_items.each(function(line_item){
                renderLineItem(line_item);
            });
        }
    }

    function renderLineItem(line_item)  {
        var line_item_view = new LineItemView({
            model: line_item,
            el: 'inventory_table'
        });
        line_item_view.renderInline();
    }

    function renderApp(app) {
        var app_view = new AppView({
            model: app,
            el: 'inventory_table'
        });
        app_view.renderInline();
    }

    function renderAdUnit(adunit) {
        var adunit_view = new AdUnitView({
            model: adunit,
            el: 'inventory_table'
        });
        adunit_view.renderInline();
    }


    /*
     * Changes the status of an ad source (or list of ad sources) to
     * `status` (which should be one of: running, paused, archived,
     * deleted). Sets up and makes the ajax call, and then updates the
     * table row once the ajax call has finished. See the
     * AdSourceStatusChangeHandler class in orders.py for more info.
     */
    function changeStatus(ad_sources, status) {

        // Show the spinner for the ad source
        _.each(ad_sources, function(ad_source) {
            $("#" + ad_source + "-img").removeClass('hidden');
        });

        // Set up
        var promise = $.ajax({
            url: '/advertise/ad_source/status/',
            type: 'POST',
            data: {
                ad_sources: ad_sources,
                status: status
            },
            cache: false,
            dataType: "json",
            success: function (data, text_status, xhr) {
                if (data.success) {
                    _.each(ad_sources, function(ad_source) {

                        // Hide the loading image
                        $("#" + ad_source + "-img").toggleClass('hidden');

                        // get the elements  we're going to edit
                        var status_img = $('#status-' + ad_source);
                        var status_change_controls = $('.status_change_control');
                        var ad_source_tds = $('#' +ad_source + ' td:not(.controls)');

                        if (status == 'play' || status == 'run') {
                            $(ad_source_tds).fadeTo(500, 1);
                            $('#' + ad_source).addClass('running')
                                .removeClass('archived')
                                .removeClass('paused');
                            $(status_img).attr('src', '/images/active.gif');

                        } else if (status == 'pause') {
                            $('#' + ad_source).addClass('paused')
                                .removeClass('archived')
                                .removeClass('running');
                            $(status_img).attr('src', '/images/paused.gif');

                        } else if (status == 'archive') {
                            $('#' + ad_source).addClass('archived')
                                .removeClass('running')
                                .removeClass('paused');
                            $(ad_source_tds).fadeTo(500, 0.4);
                            $(status_img).attr('src', '/images/archived.gif');

                        } else if (status == 'delete') {
                            $(ad_source_tds).fadeTo(500, 0.4);
                            $(status_img).attr('src', '/images/deleted.gif');
                        }
                    });
                } else {
                    _.each(ad_sources, function(ad_source) {
                        $("#" + ad_source + "-img").addClass('hidden');
                    });
                }
            },
            error: function (data, text_status, xhr) {
                _.each(ad_sources, function(ad_source) {
                    $("#" + ad_source + "-img").addClass('hidden');
                });
                // Pop up a toast?
            }
        });
    }

    /*
     * Hides all table rows in `table_id` that don't have the class
     * `filter_by`. Used to filter orders/line items by their status
     * (running/paused/scheduled/completed/archived).
     */
    function filterLineItems(filter_by, table_id) {

        var table = $(table_id);
        var table_rows = $('tr.lineitem-row', table);

        _.each(table_rows, function(table_row) {
            $(table_row).hide();
        });
        _.each(table_rows, function(table_row) {
            if ($(table_row).hasClass(filter_by)){
                $(table_row).show(500);
            }
        });
    }


    function copyLineItem(line_item_key, order_key, with_creatives) {

        var error_message = "MoPub experienced an error "
            + "trying to copy your line item. "
            + "We apologize for this inconvenience. "
            + "If this error persists, please contact "
            + "support@mopub.com";

        // Hit the copy endpoint with our form data
        var copy_promise = $.ajax({
            url: '/advertise/line_item_copy/',
            type: 'post',
            data: {
                order: order_key,
                line_item: line_item_key,
                copy_creatives: with_creatives
            }
        });

        // If we got a response, and there was a success message,
        // let them know in a toast message that points to the new
        // copied line item. Otherwise, show the error message.
        copy_promise.success(function(response) {
            if (response.success) {
                var message = "Your line  was successfully copied."
                    + "You can see your new line item <a href='" + response.url
                    + "'>here</a>.";
                Toast.success(message);
            } else {
                console.log(response);
                Toast.error(error_message);
            }

        });

        // We blew it.
        copy_promise.error(function(response) {
            console.log(response);
            Toast.error(error_message);
        });

        return copy_promise;
    }

    /*
     * Sets up the click handler for the status control button. This
     * is the button group that pauses, resumes, and archives
     * orders/line items/creatives.
     */
    function initializeStatusControls() {
        $(".status_change.btn").click(function(e){
            e.preventDefault();
            var status = $(this).attr('data-toggle');
            var checked_adgroups = $(".status_change_control:checked");
            var keys = _.map(checked_adgroups, function (row) {
                return $(row).attr('id');
            });

            changeStatus(keys, status);
            $(".status_change_control").each(function(){
                $(this).attr('checked', false);
            });
        });
    }

    /*
     * Initializes the hiding/showing of line items in a table
     * based on their status (running/scheduled/completed/etc).
     */
    function initializeLineItemFilters() {
        $(".filter-toggle").click(function(e) {
            e.preventDefault();
            var toggled = $('i.toggle-check', $(this));
            if (!toggled.hasClass('invisible')){
                toggled.addClass('invisible');
                filterLineItems("lineitem-row", "#line_item_table");
            } else {
                $('.toggle-check').addClass('invisible');
                filterLineItems($(this).attr('data-toggle'), "#line_item_table");
                $('i.toggle-check', $(this)).removeClass('invisible');
            }
        });

        $("#filter-button").click(function(e) {
            e.preventDefault();
            filterLineItems("lineitem-row", "#line_item_table");
        });

    }


    /*
     * This definitely should be moved to something common.
     */
    function initializeDateButtons() {
        // set up stats breakdown dateOptions
        $('#stats-breakdown-dateOptions input').click(function() {
            $('.stats-breakdown-value').hide();
            $('.stats-breakdown-value.'+$(this).val()).show();
        });
    }


    /*
     * # OrdersController is the controller for everything
     *   under /advertise/orders/, including:
     * - /advertise/orders/  (`initializeIndex`)
     * - /advertise/order/<key>  (`initializeOrderDetail`)
     * - /advertiser/line_item/<key>  (`initializeLineItemDetail`)
     */
    var OrdersController = {

        /*
         * Renders everything in the
         */
        initializeIndex: function(bootstrapping_data) {
            initializeStatusControls();
            initializeLineItemFilters();

            // Fetch stats for each order and render the row
            _.each(bootstrapping_data.order_keys, function (order_key) {
                var order = new Order({
                    id: order_key,
                });

                order.bind('change', function() {
                    renderOrder(order, false);
                });

                order.fetch();
            });

            // Fetch stats for each line item and render the row
            _.each(bootstrapping_data.line_item_keys, function (line_item_key) {
                var line_item = new LineItem({
                    id: line_item_key,
                });

                line_item.bind('change', function() {
                    renderLineItem(line_item);
                });

                line_item.fetch();
            });


            /*
             * Clear the checked rows when you click a different tab.
             */
            $("ul.tabs").click(function() {
                $(".status_change_control").each(function(){
                    $(this).attr('checked', false);
                });
            });


            // Set up the quick jump dropdowns
            $("#order-quick-navigate").chosen().change(function() {
                window.location = $(this).val();
            });

            // Set up the quick jump dropdown
            $("#line-item-quick-navigate")
                .chosen()
                .change(function() {
                    window.location = $(this).val();
                });
        },

        initializeOrderDetail: function(bootstrapping_data) {
            initializeStatusControls();
            initializeLineItemFilters();
            initializeDateButtons();

            /*
             * Set up the order form validator
             */
            var validator = $('form#order_form').validate({
                errorPlacement: function(error, element) {
                    element.closest('div').append(error);
                },
                submitHandler: function(form) {
                    $(form).ajaxSubmit({
                        data: {ajax: true},
                        dataType: 'json',
                        success: function(jsonData, statusText, xhr, $form) {
                            if(jsonData.success) {
                                window.location.reload();
                                $('form#order_form #submit').button({
                                    label: 'Success...',
                                    disabled: true
                                });
                            } else {
                                validator.showErrors(jsonData.errors);
                                $('form#order_form #submit').button({
                                    label: 'Try Again',
                                    disabled: false
                                });
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            $('form#order_form #submit').button({
                                label: 'Try Again',
                                disabled: false
                            });
                        },
                        beforeSubmit: function(arr, $form, options) {
                            $('form#order_form #submit').button({
                                label: 'Submitting...',
                                disabled: true
                            });
                        }
                    });
                }
            });

            /*
             * Load all of the order and line item stats
             */

            // Fill in stats for the order/line item table
            var order = new Order({
                id: bootstrapping_data.order_key
            });
            order.url = function () {
                return '/api/campaign/'
                    + this.id
                    + '?s=' + bootstrapping_data.start_date.getFullYear() + '-' + (bootstrapping_data.start_date.getMonth() + 1) + '-' + bootstrapping_data.start_date.getDate()
                    + '&r=' + bootstrapping_data.date_range
                    + '&endpoint=direct';
            };

            order.bind('change', function(current_order) {
                // Render the order row
                renderOrder(order);

                // Make the chart. The chart takes a collection as a parameter,
                // so we add the single order to a collection.
                var orders = new OrderCollection();
                orders.add(order);

                var start_date2 = new Date(bootstrapping_data.start_date);

                var chart_view = new CollectionChartView({
                    collection: orders,
                    start_date: start_date2,
                    display_values: ['imp', 'clk', 'ctr', 'conv']
                });
                chart_view.render();

                // // Load the daily counts
                // var daily_counts_view = new DailyCountsView({
                //     model: order
                // });
                // daily_counts_view.render();
            });

            order.fetch();


            /*
             * Load the data in the targetting table
             */

            // Fill in stats for the targeted apps
            // _.each(bootstrapping_data.targeted_apps, function(app_key) {
            //     var app = new App({
            //         id: app_key,
            //         stats_endpoint: 'direct'
            //     });

            //     app.url = function () {
            //         return '/api/campaign/'
            //             + bootstrapping_data.order_key
            //             + '/apps/'
            //             + this.id
            //             + "?"
            //             + window.location.search.substring(1)
            //             + '&endpoint=direct';
            //     };

            //     app.bind('change', function(current_app){
            //         renderApp(current_app);
            //     });
            //     app.fetch();
            // });

            // Fill in the stats for the targeted adunits
            // _.each(bootstrapping_data.targeted_adunits, function(adunit_key) {
            //     var adunit = new AdUnit({
            //         id: adunit_key,
            //         stats_endpoint: 'direct'
            //     });
            //     adunit.url = function () {
            //         return '/api/campaign/'
            //             + bootstrapping_data.order_key
            //             + '/adunits/'
            //             + this.id
            //             + "?"
            //             + window.location.search.substring(1)
            //             + '&endpoint=direct';
            //     };
            //     adunit.bind('change', function(current_adunit){
            //         renderAdUnit(current_adunit);
            //     });

            //     adunit.fetch();
            // });


            /*
             * Click Handlers // Miscellaneous
             */

            // Sets up the click handler for the order form
            $("#order_form_edit").click(function(e){
                e.preventDefault();
                $("#order_form_container").show();
            });

            // submit button
            $('#order_form #submit').click(function(e) {
                e.preventDefault();
                $('form#order_form').submit();
            });
        },

        initializeLineItemDetail: function(bootstrapping_data) {

            initializeDateButtons();
            initializeStatusControls();

            /*
             * Load the stats for the line item
             */

            var line_item = new LineItem({
                id: bootstrapping_data.line_item_key
            });
            line_item.url = function () {
                return '/api/adgroup/'
                    + this.id
                    + '?s=' + bootstrapping_data.start_date.getFullYear() + '-' + (bootstrapping_data.start_date.getMonth() + 1) + '-' + bootstrapping_data.start_date.getDate()
                    + '&r=' + bootstrapping_data.date_range
                    + '&endpoint=direct';
            };

            line_item.bind('change', function (current_line_item) {

                renderLineItem(current_line_item);

                var line_items = new LineItemCollection();
                line_items.add(line_item);

                var chart_view = new CollectionChartView({
                    collection: line_items,
                    start_date: bootstrapping_data.start_date,
                    display_values: ['imp', 'clk', 'ctr', 'conv']
                });
                chart_view.render();

                // // Load the daily counts
                // var daily_counts_view = new DailyCountsView({
                //     model: line_item
                // });
                // daily_counts_view.render();
            });

            line_item.fetch();

            /*
             * Load the data in the targetting table
             */

            // Get all of the apps that are targeted by this line item
            // and fill in their stats in the targeted table.
            // _.each(bootstrapping_data.targeted_apps, function(app_key) {
            //     var app = new App({
            //         id: app_key,
            //         stats_endpoint: 'direct'
            //     });

            //     app.url = function () {
            //         var stats_endpoint = this.get('stats_endpoint');
            //         return '/api/adgroup/'
            //             + bootstrapping_data.line_item_key
            //             + '/apps/'
            //             + this.id
            //             + "?"
            //             + window.location.search.substring(1)
            //             + '&endpoint='
            //             + stats_endpoint;
            //     };

            //     app.bind('change', function(current_app){
            //         renderApp(current_app);
            //     });
            //     app.fetch();
            // });

            // Same deal with the adunits. Get all of the adunits that are
            // targeted by this line item and fill in their stats in the
            // targeted table.
            // _.each(bootstrapping_data.targeted_adunits, function(adunit_key) {
            //     var adunit = new AdUnit({
            //         id: adunit_key,
            //         stats_endpoint: 'direct'
            //     });

            //     adunit.url = function () {
            //         var stats_endpoint = this.get('stats_endpoint');
            //         return '/api/adgroup/'
            //             + bootstrapping_data.line_item_key
            //             + '/adunits/'
            //             + this.id
            //             + "?"
            //             + window.location.search.substring(1)
            //             + '&endpoint='

            //             + stats_endpoint;
            //     };

            //     adunit.bind('change', function(current_adunit){
            //         renderAdUnit(current_adunit);
            //     });

            //     adunit.fetch();
            // });

            // Set up the handler for the copy button
            var copy_modal = $("#copy_modal").modal({
                show: false,
                keyboard: false,
                backdrop: true
            });

            $("#copy-to-order").chosen();

            $("#copy-line-item .copy_option").click(function () {

                var $option = $(this),
                    toggle = $option.data('toggle');

                // Quick copy with creatives. No need to show a modal.
                if (toggle === 'copy_with') {
                    var promise = copyLineItem(bootstrapping_data.line_item_key,
                                               bootstrapping_data.order_key,
                                               true);

                // Quick copy with creatives. No need to show a modal.
                } else if (toggle === 'copy_without') {
                    var promise = copyLineItem(bootstrapping_data.line_item_key,
                                               bootstrapping_data.order_key,
                                               false);


                } else if (toggle === 'copy_to_another') {
                    // Copy with more options. Show a modal.

                    // Set the default value for the order dropdown to
                    // the line item's current order.
                    $("#copy-to-order").val(bootstrapping_data.order_key);

                    // Open the modal
                    copy_modal.modal('show');

                    // On submit, grab the form data and post it over ajax
                    $("#copy-ok-button").click(function () {

                        $("#modal-loading-img").removeClass('hidden');
                        var order = $("#copy-to-order").val();
                        var copy_creatives = $("#copy_with_creatives").is(":checked");
                        var promise = copyLineItem(bootstrapping_data.line_item_key,
                                                   order,
                                                   copy_creatives);

                        promise.done(function () {
                            $("#modal-loading-img").addClass('hidden');
                        });
                    });

                } else {
                    throw Error('malformed data toggle');
                }

            });


            /*
             * Click handlers for the creative form.
             */

            // format
            $('[name="format"]').change(function() {
                var format = $(this).val();
                $('.format_dependent', $(this).closest('form')).each(function() {
                    $(this).toggle($(this).hasClass(format));
                });
            }).change();

            // ad_type
            $('[name="ad_type"]').change(function() {
                var ad_type = $(this).val();
                $('.ad_type_dependent', $(this).closest('form')).each(function() {
                    $(this).toggle($(this).hasClass(ad_type));
                });
            }).filter(':checked').change();

            // text_icon advanced
            $('#advanced_fields_button').click(function() {
                var list = $('ul#advanced_fields_list', $(this).closest('form'));
                if (list.is(":visible")) {
                    list.slideUp();
                    $(this).html('More Options');
                } else {
                    list.slideDown();
                    $(this).html('Less Options');
                }
            });

            // help links
            $('a.help_link').click(function(evt) {
                evt.preventDefault();
                $(this).next('div.help_content').dialog({
                    buttons: { 'Close': function() { $(this).dialog('close'); } }
                });
            });

            /* NEW CREATIVE FORM */
            // new creative button
            $('button#new_creative_button').click(function() {
                $(this).hide();
                $('form#new_creative_form').slideDown();
            });

            var validator = $('form#new_creative_form').validate({
                errorPlacement: function(error, element) {
                    // when submitted through an iFrame to allow file upload,
                    // the wrong element is selected, so get the correct one
                    element = $('form#new_creative_form *[name="' + element.attr('name') + '"]"');
                    element.closest('div').append(error);
                },
                submitHandler: function(form) {
                    $(form).ajaxSubmit({
                        dataType: 'json',
                        beforeSubmit: function(data, $form, options) {
                            var button = $('.submit', $form);
                            button.html('Submitting...');
                            button.attr('disabled', 'disabled');
                        },
                        success: function(data, textStatus, jqXHR, $form) {
                            var button = $('.submit', $form);
                            if(data.success) {
                                window.location = data.redirect;
                                button.html('Success...');
                            } else {
                                validator.showErrors(data.errors);
                                button.html('Try Again');
                                button.removeAttr('disabled');
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            $('form#new_creative_form .submit').button({
                                label: 'Try Again',
                                disabled: false
                            });
                        }
                    });
                }
            });

            // cancel button
            $('form#new_creative_form button.cancel').click(function(evt) {
                evt.preventDefault();
                $('button#new_creative_button').show();
                $('form#new_creative_form').slideUp();
            });

            // submit button
            $('form#new_creative_form .submit').click(function(evt) {
                evt.preventDefault();
                $('form#new_creative_form').submit();
            });

            /* EDIT CREATIVE FORMS */
            // creative preview button
            $('#creative_preview_button').click(function(e) {
                e.preventDefault();
                var modal = $(this).siblings('div#creative_preview');
                var preview = modal.children('div.modal-body');
                var src = preview.children('input[name="src"]').val();
                var iframe = preview.children('iframe');
                iframe.attr('src', src);
                var width = parseInt(iframe.attr("width"));
                var height = parseInt(iframe.attr("height"));
                modal.css({
                    'width': 'auto',
                    'height': 'auto',
                    'margin-left': function () {
                        return -($(this).width() / 2);
                    },
                    'margin-top': function () {
                        return -($(this).height() / 2);
                    }
                });
                modal.modal('show');
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

            // edit creative button
            $('button.edit_creative_button').click(function() {
                $(this).hide();
                $(this).siblings('form.edit_creative_form').slideDown();
            });

            // TODO: a lot of this is duplicated from above
            _.each($('form.edit_creative_form'), function(form) {
                var validator = $(form).validate({
                    errorPlacement: function(error, element) {
                        // when submitted through an iFrame to allow file upload,
                        // the wrong element is selected, so get the correct one
                        element = $('*[name="' + element.attr('name') + '"]"', $(form));
                        element.closest('div').append(error);
                    },
                    submitHandler: function(form) {
                        $(form).ajaxSubmit({
                            dataType: 'json',
                            beforeSubmit: function(data, $form, options) {
                                var button = $('button.submit', $form);
                                button.html('Submitting...');
                                button.attr('disabled', 'disabled');
                            },
                            success: function(data, textStatus, jqXHR, $form) {
                                var button = $('button.submit', $form);
                                if(data.success) {
                                    window.location = data.redirect;
                                    button.html('Success...');
                                } else {
                                    validator.showErrors(data.errors);
                                    button.html('Try Again');
                                    button.removeAttr('disabled');
                                }
                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                $('button.submit', $(form)).button({
                                    label: 'Try Again',
                                    disabled: false
                                });
                            }
                        });
                    }
                });
            });

            // cancel button
            $('form.edit_creative_form button.cancel').click(function(evt) {
                evt.preventDefault();
                $(this).closest('form.edit_creative_form').siblings('button.edit_creative_button').show();
                $(this).closest('form.edit_creative_form').slideUp();
            });

            // submit button
            $('form.edit_creative_form .submit').click(function(evt) {
                evt.preventDefault();
                $(this).closest('form.edit_creative_form').submit();
            });
        },

        initializeOrderAndLineItemForm: function(bootstrapping_data) {
            var validator = $('#order_and_line_item_form').validate({
                errorPlacement: function(error, element) {
                    element.closest('div').append(error);
                },
                submitHandler: function(form) {
                    $(form).ajaxSubmit({
                        data: {ajax: true},
                        dataType: 'json',
                        success: function(jsonData, statusText, xhr, $form) {
                            if(jsonData.success) {
                                window.location = jsonData.redirect;
                                $('form#order_and_line_item_form #submit').button({
                                    label: 'Success...',
                                    disabled: true
                                });
                            } else {
                                console.log(jsonData.errors);
                                validator.showErrors(jsonData.errors);
                                $('form#order_and_line_item_form #submit').button({
                                    label: 'Try Again',
                                    disabled: false
                                });
                            }
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            $('form#order_and_line_item_form #submit').button({
                                label: 'Try Again',
                                disabled: false
                            });
                        },
                        beforeSubmit: function(arr, $form, options) {
                            $('form#order_and_line_item_form #submit').button({
                                label: 'Submitting...',
                                disabled: true
                            });
                        }
                    });
                }
            });

            // submit button
            $('form#order_and_line_item_form #submit').button({
                icons: {secondary: 'ui-icon-circle-triangle-e'}
            });
            $('form#order_and_line_item_form #submit').click(function(e) {
                e.preventDefault();
                $('form#order_and_line_item_form').submit();
            });

            // toggle fields based on adgroup_type
            $('[name="adgroup_type"]').change(function() {
                var adgroup_type = $(this).val();
                $('.adgroup_type_dependent').each(function() {
                    $(this).toggle($(this).hasClass(adgroup_type));
                });
            }).change(); // update on document ready

            // help links
            // TODO: make sure all of these are necessary, rename?
            $('a[id$="-helpLink"]').click(function(e) {
                e.preventDefault();
                $('#' + $(this).attr('id').replace('-helpLink', '-helpContent')).dialog({
                    buttons: { "Close": function() { $(this).dialog("close"); } }
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

                var hour = matchArray[1];
                var minute = matchArray[2];
                var ampm = matchArray[4];

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

            $('input[name="end_datetime_0"], input[name="end_datetime_1"], select[name="budget_type"], select[name="budget_strategy"]').change(function(){
                if(!$('input[name="end_datetime_0"]').val() &&
                   !$('input[name="end_datetime_1"]').val() &&
                   $('select[name="budget_type"]').val() == 'full_campaign') {
                    $('input#id_budget_strategy_1').prop('checked', 'checked');
                    $('input#id_budget_strategy_0').removeProp('checked');
                    $('input#id_budget_strategy_0').attr('disabled', 'disabled');
                }
                else {
                    $('input#id_budget_strategy_0').removeAttr('disabled');
                }
            }).change();

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
            if($('input[name="device_targeting"]:checked').val() == '0') {
                $('#device_targeting').hide();
            }

            // change form based on bid_strategy
            $('select[name="bid_strategy"]').change(function() {
                var bid_strategy = $(this).val();
                var budget_type_options = $('select[name="budget_type"] option');
                if(bid_strategy == 'cpm') {
                    budget_type_options[0].innerHTML = 'impressions/day';
                    budget_type_options[1].innerHTML = 'total impressions';
                }
                else {
                    budget_type_options[0].innerHTML = 'USD/day';
                    budget_type_options[1].innerHTML = 'total USD';
                }
            }).change(); // update on document ready

            $('select[name="budget_type"]').change(function() {
                var budget_type = $(this).val();
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
                        $(this).text('Hide Advanced Targeting');
                    } else {
                        $('fieldset#advanced').slideUp('fast');
                        $(this).button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
                        $(this).text('Show Advanced Targeting');
                    }
                }); // TODO: need to update on document ready

            /* GEO TARGETING */
            var geo_s = 'http://api.geonames.org/searchJSON?username=MoPub&';
            var pre = {type: 'country', data: []};
            var city_pre = {type: 'city', data: []};
            //Not being used right now
            //var state_pre = {type: 'state', data: []};

            for(var index in countries) {
                var dat = countries[index];
                if($.inArray(dat.code, bootstrapping_data.priors) != -1) {
                    pre.data.push(dat);
                }
                if(pre.length == bootstrapping_data.priors.length)
                    break;
            }

            //city is ll:ste:name:ccode;
            for(var i in bootstrapping_data.city_priors) {
                if(bootstrapping_data.city_priors.hasOwnProperty(i)) {
                    var datas = bootstrapping_data.city_priors[i].split(':');
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


            // Show location-dependent fields when location targeting is turned on
            $('input[name="region_targeting"]').click(function(e) {
                var loc_targ = $(this).val();
                $('.locationDependent').hide();
                $('.' + loc_targ + '.locationDependent').show();
                if ($(this).val() == 'all') {
                    $('li.token-input-city span.token-input-delete-token').each(function() {
                        $(this).click();
                    });
                }
            }).filter(':checked').click();
        }
    };

    mopub.Controllers.OrdersController = OrdersController;

})(window.jQuery, window.mopub || { Controllers: {} });
