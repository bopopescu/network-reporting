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
				    //container.togglebutton.button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
				    setButtonTextElement(container.togglebutton, container.togglebutton.hideText);
			    }
			    
			    function didHideContainer(container) {
				    container.removeClass('show');
				    container.addClass('hide');
				    //container.togglebutton.button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
				    setButtonTextElement(container.togglebutton, container.togglebutton.showText);
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
    
    window.LoginController = LoginController;
    window.RegistrationController = RegistrationController;
})(this.jQuery);
