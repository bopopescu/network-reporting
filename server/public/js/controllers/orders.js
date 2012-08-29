(function () {
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
            line_items.each(function (line_item) {
                renderLineItem(line_item, false);
            });
        }
    }

    function renderLineItem(line_item, render_creatives) {
        if (typeof render_creatives === 'undefined') {
            render_creatives = true;
        }

        var line_item_view = new LineItemView({
            model: line_item,
            el: 'inventory_table'
        });
        line_item_view.renderInline();

        if (render_creatives) {
            var creatives = new CreativeCollection(line_item.get('creatives'));
            creatives.each(function (creative) {
                renderCreative(creative);
            });
        }
    }

    function renderCreative(creative) {
        var creative_view = new CreativeView({
            model: creative,
            el: 'inventory_table'
        });
        creative_view.renderInline();
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
            $("#" + ad_source + "-img").removeClass('hidden').show();
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
                        $("#" + ad_source + "-img").hide();

                        // get the elements  we're going to edit
                        var status_img = $('#status-' + ad_source);
                        var status_text = $("#text-" + ad_source);
                        var ad_source_row = $("#" + ad_source);
                        var ad_source_tds = $('#' + ad_source + ' td:not(.controls)');

                        if (status == 'play' || status == 'run') {
                            ad_source_tds.fadeTo(500, 1);
                            ad_source_row.addClass('running')
                                .removeClass('archived')
                                .removeClass('paused');
                            status_img.attr('src', '/images/active.gif');
                            status_text.text("Running");

                        } else if (status == 'pause') {
                            ad_source_tds.fadeTo(500, 1);
                            ad_source_row.addClass('paused')
                                .removeClass('archived')
                                .removeClass('running');
                            status_img.attr('src', '/images/paused.gif');
                            status_text.text("Paused");

                        } else if (status == 'archive') {
                            ad_source_row.addClass('archived')
                                .removeClass('running')
                                .removeClass('paused');
                            ad_source_tds.fadeTo(500, 0.4);
                            status_img.attr('src', '/images/archived.gif');
                            status_text.text("Archived");

                        } else if (status == 'delete') {
                            ad_source_tds.fadeTo(500, 0.4);
                            status_img.attr('src', '/images/deleted.gif');
                            status_text.text("Deleted");
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

        $("#copy-button").addClass('disabled');

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
                var message = "Your line item was successfully copied."
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

        // Re-enable the button no matter what
        copy_promise.done(function(response) {
            console.log('reenabling');
            $("#copy-button").removeClass('disabled');
        });

        return copy_promise;
    }

    function initializeBudgetControls(line_item_key) {

        $("#update-budget").click(function () {

            var use_staging = $("#use_staging").is(":checked");
            var budget_promise = $.ajax({
                url: '/advertise/push_budget/',
                data: {
                    adgroup_key: line_item_key,
                    staging: use_staging ? 1 : 0
                }

            });

            budget_promise.success(function (response) {
                Toast.info(response.status);
                $("#budget-admin-modal").modal('hide');
            });

            budget_promise.error(function (response) {
                Toast.error("Couldn't access the push endpoint");
            });
        });
    }

    /*
     * Sets up the click handler for the status control button. This
     * is the button group that pauses, resumes, and archives
     * orders/line items/creatives.
     *
     * `keep_checked` -- if True, status change control check boxes
     * will stay checked after their status is changed. Default is
     * False.
     */
    function initializeStatusControls(keep_checked) {

        if (typeof keep_checked === 'undefined') {
            keep_checked = false;
        }

        $(".status_change.btn").click(function(e){
            e.preventDefault();

            // Figure out which objects to change the status of,
            // and what we should change the status to. If either one
            // is undefined, stop.
            var table_selector = $(this).attr('data-target');
            var status = $(this).attr('data-toggle');

            if (typeof table_selector === "undefined") {
                throw Error("Status change button's data-target attribute "
                            + "cannot be undefined");
            }

            if (typeof status === "undefined") {
                throw Error("Status change button's data-toggle "
                            + "attribute cannot be undefined");
            }

            // Get the keys for the objects we're going to change
            // the status of
            var checked_adgroups = $(".status_change_control:checked",
                                     $(table_selector));
            var keys = _.map(checked_adgroups, function (row) {
                return $(row).attr('id');
            });

            // Do it
            changeStatus(keys, status);

            // In some cases we don't want to uncheck the boxes.
            if (!keep_checked) {
                $(".status_change_control").each(function(){
                    $(this).attr('checked', false);
                });
            }
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
                    include_adgroups: true
                });

                order.bind('change', function() {
                    renderOrder(order, true);
                });

                order.fetch();
            });

            /*
            // Fetch stats for each line item and render the row
            _.each(bootstrapping_data.line_item_keys, function (line_item_key) {
                var line_item = new LineItem({
                    id: line_item_key
                });

                line_item.bind('change', function() {
                    renderLineItem(line_item, false);
                });

                line_item.fetch();
            });
            */

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
            $("#line-item-quick-navigate").chosen().change(function() {
                window.location = $(this).val();
            });
        },

        initializeArchive: function (bootstrapping_data) {
            $("#delete-button").click(function (event) {
                event.preventDefault();

                // Get the keys of the checked orders/line items
                var checked_adgroups = $(".status_change_control:checked");
                var keys = _.map(checked_adgroups, function (row) {
                    return $(row).attr('id');
                });

                // Show the modal
                $("#confirm_delete_modal").modal("show");

                // On click of the confirm delete buttons,
                // delete the orders/line items
                $("#confirm_delete_button").click(function () {
                    changeStatus(keys, 'delete');
                    $("#confirm_delete_modal").modal("hide");
                });
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
                id: bootstrapping_data.order_key,
                include_daily: true,
                include_adgroups: true,
                start_date: bootstrapping_data.start_date,
                date_range: bootstrapping_data.date_range
            });

            order.bind('change', function(current_order) {
                // Render the order row
                renderOrder(order, true);

                // Make the chart. The chart takes a collection as a parameter,
                // so we add the single order to a collection.
                var orders = new OrderCollection();
                orders.add(order);

                var chart_view = new CollectionChartView({
                    collection: orders,
                    start_date: new Date(bootstrapping_data.start_date.getTime()),
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
            initializeStatusControls(true);
            initializeBudgetControls(bootstrapping_data.line_item_key);

            /*
             * Load the stats for the line item
             */

            var line_item = new LineItem({
                id: bootstrapping_data.line_item_key,
                include_daily: true,
                include_creatives: true,
                start_date: bootstrapping_data.start_date,
                date_range: bootstrapping_data.date_range
            });

            line_item.bind('change', function (current_line_item) {
                renderLineItem(current_line_item, true);

                var line_items = new LineItemCollection();
                line_items.add(line_item);

                var chart_view = new CollectionChartView({
                    collection: line_items,
                    start_date: new Date(bootstrapping_data.start_date.getTime()),
                    display_values: ['imp', 'clk', 'ctr', 'conv']
                });
                chart_view.render();

            });

            line_item.fetch();



            /*
             * Load the data in the targetting table
             */

            // Get all of the apps that are targeted by this line item
            // and fill in their stats in the targeted table.
            _.each(bootstrapping_data.targeted_apps, function(app_key) {
                var app = new App({
                    id: app_key,
                    stats_endpoint: 'direct'
                });

                app.url = function () {
                    var stats_endpoint = this.get('stats_endpoint');
                    return '/api/adgroup/'
                        + bootstrapping_data.line_item_key
                        + '/apps/'
                        + this.id
                        + "?"
                        + window.location.search.substring(1)
                        + '&endpoint='
                        + stats_endpoint;
                };

                app.bind('change', function(current_app){
                    renderApp(current_app);
                });
                app.fetch();
            });

            // Same deal with the adunits. Get all of the adunits that are
            // targeted by this line item and fill in their stats in the
            // targeted table.
            _.each(bootstrapping_data.targeted_adunits, function(adunit_key) {
                var adunit = new AdUnit({
                    id: adunit_key,
                    stats_endpoint: 'direct'
                });

                adunit.url = function () {
                    var stats_endpoint = this.get('stats_endpoint');
                    return '/api/adgroup/'
                        + bootstrapping_data.line_item_key
                        + '/adunits/'
                        + this.id
                        + "?"
                        + window.location.search.substring(1)
                        + '&endpoint='

                        + stats_endpoint;
                };

                adunit.bind('change', function(current_adunit){
                    renderAdUnit(current_adunit);
                });

                adunit.fetch();
            });

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

            // Creative Preview
            $('#creative_table button.preview').click(function () {
                var $modal = $(this).siblings('div.modal.preview');
                var $iframe = $modal.find('iframe');
                if(!$iframe.attr('src')) {
                    var src = $modal.find('input').val();
                    $iframe.attr('src', src);
                    $iframe.load(function () {
                        $iframe.css('background-image', 'none');
                    })
                }

                // Set up the modal that contains the iframe
                var width = parseInt($iframe.attr("width"));
                var height = parseInt($iframe.attr("height"));
                $modal.css({
                    'width': 'auto',
                    'height': 'auto',
                    'margin-left': function () {
                        return -($(this).width() / 2);
                    },
                    'margin-top': function () {
                        return -($(this).height() / 2);
                    }
                });
            });

            // Edit Creative
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
            $('[name="adgroup_type"]').change(function () {
                var adgroup_type = $(this).val();
                $('.adgroup_type_dependent').each(function () {
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

            $('input[name="end_datetime_0"], input[name="end_datetime_1"], select[name="budget_type"], input[name="budget_strategy"]').change(function (){
                if(!$('input[name="end_datetime_0"]').val() &&
                   !$('input[name="end_datetime_1"]').val()) {
                    if($('select[name="budget_type"]').val() == 'full_campaign') {
                        $('input[name="budget_strategy"][value="evenly"]').attr('disabled', 'disabled');
                        return;
                    }
                    if($('input[name="budget_strategy"][value="evenly"]').prop('checked')) {
                        $('select[name="budget_type"] option[value="full_campaign"]').attr('disabled', 'disabled');
                        return;
                    }
                }

                $('select[name="budget_type"] option[value="full_campaign"]').removeAttr('disabled');
                $('input[name="budget_strategy"][value="evenly"]').removeAttr('disabled');
            }).change();

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


            /*
             * Targeting
             */

            $('#all-adunits').change(function() {
                // select or deselect all adunits
                $('input[name="site_keys"]').prop('checked', $(this).prop('checked'));
            });


            /*
             * Device Targeting
             */

            $('input[name="device_targeting"]').change(function () {
                if($(this).val() == '0') {
                    $('#device_targeting_details').slideUp();
                }
                else {
                    $('#device_targeting_details').slideDown();
                }
            });
            // update on document ready
            if($('input[name="device_targeting"]:checked').val() == '0') {
                $('#device_targeting_details').hide();
            }


            /*
             * Geographical and Connectivity Targeting
             */

            /* Elements */
            var $targeted_countries = $('#id_targeted_countries');
            var $targeted_regions = $('#id_targeted_regions');
            var $targeted_cities = $('#id_targeted_cities');
            var $targeted_zip_codes = $('#id_targeted_zip_codes');
            var $targeted_carriers = $('#id_targeted_carriers');

            var $region_targeting_type_all = $('#id_region_targeting_type_0');
            var $region_targeting_type_regions_and_cities = $('#id_region_targeting_type_1');
            var $region_targeting_type_zip_codes = $('#id_region_targeting_type_2');

            var $connectivity_targeting_type_all = $('#id_connectivity_targeting_type_0');
            var $connectivity_targeting_type_carriers = $('#id_connectivity_targeting_type_2');

            /* Helpers */
            function update_geographical_and_connectivity_targeting() {
                var us_is_targeted = country_is_targeted('US');
                var ca_is_targeted = country_is_targeted('CA');
                var gb_is_targeted = country_is_targeted('GB');
                var wifi_is_targeted = $('input[name="connectivity_targeting_type"]:checked').val() != 'carriers';

                update_regions_and_cities(us_is_targeted, ca_is_targeted, wifi_is_targeted);
                update_zip_codes(us_is_targeted, wifi_is_targeted);
                update_carriers(us_is_targeted, ca_is_targeted, gb_is_targeted);
            }

            function update_regions_and_cities(us_is_targeted, ca_is_targeted, wifi_is_targeted) {
                if(!us_is_targeted && !(ca_is_targeted && wifi_is_targeted)) {
                    // remove selection
                    if($region_targeting_type_regions_and_cities.is(':checked')) {
                        $region_targeting_type_all.click();
                    }

                    // disable
                    $region_targeting_type_regions_and_cities.attr('disabled', true);
                    $region_targeting_type_regions_and_cities.parent().addClass('muted');
                }
                else {
                    // enable
                    $region_targeting_type_regions_and_cities.removeAttr('disabled');
                    $region_targeting_type_regions_and_cities.parent().removeClass('muted');
                }

                update_regions(us_is_targeted, ca_is_targeted, wifi_is_targeted);
                update_cities(us_is_targeted);
            }

            function update_regions(us_is_targeted, ca_is_targeted, wifi_is_targeted) {
                if((!us_is_targeted && !ca_is_targeted) || !wifi_is_targeted) {
                    // clear
                    $targeted_regions.html('');

                    // disable
                    $targeted_regions.attr('disabled', true);
                }
                else {
                    if(us_is_targeted) {
                        add_options($targeted_regions, bootstrapping_data.US_STATES);
                        add_options($targeted_regions, bootstrapping_data.US_METROS);
                    }
                    else {
                        remove_options($targeted_regions, bootstrapping_data.US_STATES);
                        remove_options($targeted_regions, bootstrapping_data.US_METROS);
                    }

                    if(ca_is_targeted) {
                        console.log('adding ca provinces');
                        add_options($targeted_regions, bootstrapping_data.CA_PROVINCES);
                    }
                    else {
                        remove_options($targeted_regions, bootstrapping_data.CA_PROVINCES);
                    }

                    // enable
                    $targeted_regions.removeAttr('disabled');
                }
                $targeted_regions.trigger("liszt:updated");
            }

            function update_cities(us_is_targeted) {
                if(!us_is_targeted) {
                    // clear
                    $targeted_cities.html('');

                    // disable
                    $targeted_cities.attr('disabled', true);
                }
                else {
                    // enable
                    $targeted_cities.removeAttr('disabled');
                }
                $targeted_cities.trigger("liszt:updated");
            }

            function update_zip_codes(us_is_targeted, wifi_is_targeted) {
                if(!us_is_targeted || !wifi_is_targeted) {
                    // clear
                    $targeted_zip_codes.val('');

                    // remove selection
                    if($region_targeting_type_zip_codes.is(':checked')) {
                        $region_targeting_type_all.click();
                    }

                    // disable
                    $region_targeting_type_zip_codes.attr('disabled', true);
                    $region_targeting_type_zip_codes.parent().addClass('muted');
                }
                else {
                    // enable
                    $region_targeting_type_zip_codes.removeAttr('disabled');
                    $region_targeting_type_zip_codes.parent().removeClass('muted');
                }
            }

            function update_carriers(us_is_targeted, ca_is_targeted, gb_is_targeted) {
                if(!us_is_targeted && !ca_is_targeted && !gb_is_targeted) {
                    // clear
                    $targeted_carriers.html('');

                    // remove selection
                    if($connectivity_targeting_type_carriers.is(':checked')) {
                        $connectivity_targeting_type_all.click();
                    }

                    // disable
                    $connectivity_targeting_type_carriers.attr('disabled', true);
                    $connectivity_targeting_type_carriers.parent().addClass('muted');
                }
                else {
                    if(us_is_targeted) {
                        add_options($targeted_carriers, bootstrapping_data.US_CARRIERS);
                    }
                    else {
                        remove_options($targeted_carriers, bootstrapping_data.US_CARRIERS);
                    }

                    if(ca_is_targeted) {
                        add_options($targeted_carriers, bootstrapping_data.CA_CARRIERS);
                    }
                    else {
                        remove_options($targeted_carriers, bootstrapping_data.CA_CARRIERS);
                    }

                    if(gb_is_targeted) {
                        add_options($targeted_carriers, bootstrapping_data.GB_CARRIERS);
                    }
                    else {
                        remove_options($targeted_carriers, bootstrapping_data.GB_CARRIERS);
                    }

                    // enable
                    $connectivity_targeting_type_carriers.removeAttr('disabled');
                    $connectivity_targeting_type_carriers.parent().removeClass('muted');
                }
                $targeted_carriers.trigger("liszt:updated");
            }

            function country_is_targeted(country) {
                return _.include($targeted_countries.val(), country);
            }

            function carrier_is_targeted(carrier) {
                return _.include($targeted_carriers.val(), carrier);
            }

            function add_options($element, options) {
                for(var index in options) {
                    var value = options[index][0];
                    if(!$('option[value="' + value + '"]', $element).length) {
                        $element.append($('<option />', {
                            value: value,
                            html: options[index][1]
                        }));
                    }
                }
            }

            function remove_options($element, options) {
                for(var index in options) {
                    var value = options[index][0];
                    $('option[value="' + value + '"]', $element).remove();
                }
            }

            /* Event Handlers */
            $targeted_countries.chosen().change(update_geographical_and_connectivity_targeting);

            $('input[name="region_targeting_type"]').click(function () {
                $('input[name="region_targeting_type"]').parent().siblings('div').hide();
                $(this).parent().siblings('div').show();
            });
            $('input[name="region_targeting_type"]:checked').click();

            $targeted_regions.chosen();

            $targeted_cities.ajaxChosen(
                {
                    dataType: 'json',
                    jsonTermKey: 'name_startsWith',
                    method: 'GET',
                    minTermLength: 3,
                    url: 'http://api.geonames.org/searchJSON?country=US&featureClass=P&maxRows=10&username=MoPub&'
                }, function (data) {
                    var terms = {};
                    for(var index in data.geonames) {
                        var geoname = data.geonames[index];
                        var key = '(' + geoname.lat + ',' + geoname.lng + ',\'' + geoname.name + '\',\'' + geoname.adminCode1 + '\',\'' + geoname.countryCode + '\')';
                        var value = geoname.name + ', ' + geoname.adminCode1;
                        terms[key] = value;
                    }
                    return terms;
                }
            );

            $('#id_connectivity_targeting_type_0, #id_connectivity_targeting_type_1').change(function () {
                $('#id_targeted_carriers').parent().hide();
                update_geographical_and_connectivity_targeting();
            });
            $connectivity_targeting_type_carriers.click(function () {
                if($targeted_regions.val() || $targeted_zip_codes.val()) {
                    event.preventDefault();
                    $('#target_carriers_warning .continue').unbind().click(function () {
                        $connectivity_targeting_type_carriers.attr('checked', 'checked');
                        $('#id_targeted_carriers').parent().show();
                        update_geographical_and_connectivity_targeting();
                    })
                    $('#target_carriers_warning').modal();
                }
                else {
                    update_geographical_and_connectivity_targeting();
                }
            });
            // update on document ready
            if($('input[name="connectivity_targeting_type"]:checked').val() != 'carriers') {
                $('#id_targeted_carriers').parent().hide();
            }

            $targeted_carriers.chosen();

            // TODO: confirmation modal

            // TODO: grey out countries

            // Initialize
            update_geographical_and_connectivity_targeting();

            _.each(bootstrapping_data.targeted_regions, function (targeted_region) {
                $('option[value="' + targeted_region + '"]', $targeted_regions).prop('selected', 'selected');
            })
            $targeted_regions.trigger("liszt:updated");

            _.each(bootstrapping_data.targeted_cities, function (targeted_city) {
                var parts = targeted_city.split(',\'');
                var name = parts[1].substring(0, parts[1].length - 1) + ', ' + parts[2].substring(0, parts[2].length - 1);
                $targeted_cities.append($('<option />', {
                    html: name,
                    selected: 'selected',
                    value: targeted_city
                }));
            });
            $targeted_cities.trigger("liszt:updated");

            _.each(bootstrapping_data.targeted_carriers, function (targeted_carrier) {
                $('option[value="' + targeted_carrier + '"]', $targeted_carriers).prop('selected', 'selected');
            })
            $targeted_carriers.trigger("liszt:updated");


            /*
             * Advanced Targeting
             */

            $('[name="included_apps"]').chosen();
            $('[name="excluded_apps"]').chosen();

            if($('[name="included_apps"] option:selected').length > 0) {
                $('#user_targeting_type').val('included_apps');
            }
            else {
                $('#user_targeting_type').val('excluded_apps');
            }

            $('#user_targeting_type').change(function() {
                var $this = $(this);
                if($this.val() == 'included_apps') {
                    $('#id_excluded_apps_chzn').hide();
                    $('[name="excluded_apps"] option:selected').removeAttr('selected');
                    $('[name="excluded_apps"]').trigger("liszt:updated");
                    $('#id_included_apps_chzn').show();
                }
                else {
                    $('#id_included_apps_chzn').hide();
                    $('[name="included_apps"] option:selected').removeAttr('selected');
                    $('[name="included_apps"]').trigger("liszt:updated");
                    $('#id_excluded_apps_chzn').show();
                }
            }).change();

        }
    };

    window.OrdersController = OrdersController;

}).call(this);
