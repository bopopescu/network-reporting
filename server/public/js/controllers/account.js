/*
	MoPub Dashboard JS
*/

// global mopub object
var mopub = mopub || {};

(function($){

    var LoginController = {
        initialize: function () {

		    $('#accountForm-submit').click(function(e) {
			    e.preventDefault();
			    $('#accountForm').submit();
		    });

            $('.formFields input').keypress(function(e) {
                if (e.which == 13) {
                    e.preventDefault();
                    $('#accountForm').submit();
                }
            });

        }
    };


    var RegistrationController = {
        initialize: function () {

            $('#paymentchange-submit').click(function(e) {
				e.preventDefault();
				$('#paymentchange').submit();
			});

		    // Hack to add the correct class to input fields
		    $('input:text').addClass('input-text');
	        $('input:password').addClass('input-text');
	        
		    $('#accountForm-submit').click(function(e) {
			    e.preventDefault();
			    $('#accountForm').submit();
		    });
            
            
		    // set up showing/hiding of app details
		    $('.adForm').each(function() {
			    var details = $(this);
			    var data = $('.formFields', details);
			    var button = $('.adForm-fields-toggleButton', details);
			    var infobutton = $('.adForm-fields-infoButton', details);
			    var infodialog = $('.accountInfoForm', details);
			    var appbutton = $('.adForm-fields-appButton', details);
			    var apps = $('.adForm-apps', details);
			    
			    data.togglebutton = button;
			    data.togglebutton.showText = 'Show details';
			    data.togglebutton.hideText = 'Hide details';
			    
			    apps.togglebutton = appbutton;
			    apps.togglebutton.showText = 'Show apps';
			    apps.togglebutton.hideText = 'Hide apps';
                
			    function getButtonTextElement(buttonElement) {
				    var buttonTextElement = $('.ui-button-text', buttonElement);
				    if(buttonTextElement.length == 0) buttonTextElement = buttonElement;
				    return buttonTextElement;
			    }
			    
			    function setButtonTextElement(buttonElement, text) {
			        getButtonTextElement(buttonElement).text(text);
			    }
                
			    function didShowContainer(container) {
				    container.removeClass('hide');
				    container.addClass('show');
				    setButtonTextElement(container.togglebutton, 
                                         container.togglebutton.hideText);
			    }
			    
			    function didHideContainer(container) {
				    container.removeClass('show');
				    container.addClass('hide');
				    setButtonTextElement(container.togglebutton, 
                                         container.togglebutton.showText);
			    }
                
			    if (data.hasClass('show')) {
				    didShowContainer(data);
			    }
			    else {
				    data.hide();
				    didHideContainer(data);
			    }
			    
			    button.click(function(e) {
				    e.preventDefault();
				    if(data.hasClass('show')) {
					    data.slideUp('fast');
					    didHideContainer(data);
				    }
				    else {
					    data.slideDown('fast');
					    didShowContainer(data);
				    }
			    });
			    
			    infobutton.click(function(e) {
				    e.preventDefault();
				    infodialog.dialog({
				        width: 570,
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
			    
			    appbutton.click(function(e) {
			        e.preventDefault();
				    if(apps.hasClass('show')) {
					    apps.slideUp('fast');
					    didHideContainer(apps);
				    } else {
					    apps.slideDown('fast');
					    didShowContainer(apps);
				    }
			    }).click();
			    
                if (apps.hasClass('show')) {
                    didShowContainer(apps);
                } else {
                    apps.hide();
                    didHideContainer(apps);
                }
			    
		    });
        }
    };


    var AccountController = {
        initializePaymentDetails: function (bootstrapping_data) {
            var paypal_required_fields = ['#id_paypal_email'];
            var us_required_fields = ['#id_us_tax_id'];
            var non_us_required_fields = [];
            var wire_required_fields = ['#id_beneficiary_name',
                                        '#id_bank_name',
                                        '#id_bank_address',
                                        '#id_account_number'];
            var us_wire_required_fields = ['#id_ach_routing_number'];
            var non_us_wire_required_fields = ['#id_bank_swift_code'];
            
            var all_wire_fields = wire_required_fields
                .concat(us_wire_required_fields)
                .concat(non_us_wire_required_fields);
            
            if ($("#payment_preference_paypal").is(":checked")) {
                $("#wire_only").hide();
            } else {
                $("#paypal_only").hide();
            }
            
            $("#payment_preference_paypal").click(function(){
                $("#wire_only").fadeOut(10);
                $("#paypal_only").fadeIn();
                $.each(paypal_required_fields, function(i, field){
                    $(field).addClass("required");
                });
                $.each(all_wire_fields, function(i, field) {
                    $(field).removeClass("required");
                });
            });

            $("#payment_preference_wire").click(function(){

                $("#paypal_only").fadeOut(10);
                $("#wire_only").fadeIn();

                $.each(paypal_required_fields, function(i, field){
                    $(field).removeClass("required");
                });

                $.each(wire_required_fields, function(i, field) {
                    $(field).addClass("required");
                });

                if ($("#id_country").val() == "US") {
                    $.each(us_wire_required_fields, function(i, field) {
                        $(field).addClass("required");
                    });
                    $.each(non_us_wire_required_fields, function(i, field) {
                        $(field).removeClass("required");
                    });
                } else {
                    $.each(us_wire_required_fields, function(i, field) {
                                    $(field).removeClass("required");
                    });
                    $.each(non_us_wire_required_fields, function(i, field) {
                        $(field).addClass("required");
                    });
                }
            });

            $("#id_country").change(function() {

                if ($("#id_country").val() == "US") {
                    $(".us_only").show();
                    $(".non_us_only").hide();
                    $.each(us_required_fields, function(i, field) {
                        $(field).addClass("required");
                    });
                    $.each(non_us_required_fields, function(i, field) {
                        $(field).removeClass("required");
                    });
                } else {
                    $(".us_only").hide();
                    $(".non_us_only").show();
                    $.each(us_required_fields, function(i, field) {
                        $(field).removeClass("required");
                    });
                    $.each(non_us_required_fields, function(i, field) {
                        $(field).addClass("required");
                    });
                }

                if ($("#payment_preference_paypal").is(":checked")) {
                    $("#payment_preference_paypal").click();
                } else {
                    $("#payment_preference_wire").click();
                }
            }).change();

            $('#paymentchange-submit').click(function(e) {
			    e.preventDefault();
			    $('#paymentchange').submit();
		    });
        }
    };
    
    window.LoginController = LoginController;
    window.RegistrationController = RegistrationController;
    window.AccountController = AccountController;

})(this.jQuery);
