(function() {

    var ua = function(browser){
        var agent = navigator.userAgent.toLowerCase();
        return agent.indexOf(browser) !== -1;
    };

    var get_browser = function() {
        if ('msie 7') {
            return 'ie7';
        }

        if ('msie 8') {
            return 'ie8';
        }

        if ('msie 9') {
            return 'ie9';
        }

        if ('msie 10') {
            return 'ie10';
        }

        if ('msie') {
            return 'ie>=6';
        }

        if (ua('opera')) {
            return 'opera';
        }

        if (ua('safari')) {
            if (ua('chrome')) {
                return 'webkit';
            }
            return 'safari';
        } else {
            if (ua('mozilla')) {
                return 'mozilla';
            }
        }

        // leave this one for last because it can appear in
        // non-chrome webkit browsers
        if (ua('chrome')) {
            return 'chrome';
        }

        return 'unorthodox';
    };

    window.Browser = {
        get_browser: get_browser
    };

})();
var retry=0;

function checkReport(retry_num) {
    //If exists returns data, otherwise returns False
    var id = $('#reportKey').val();

    if (id){
        $.ajax({
           url: '/reports/check/'+id+'/?retry='+retry_num,
           success: writeReport
        });
    }
}

function writeReport(report) {
    if (report.data == 'none') {
        retry++;
        setTimeout('checkReport('+retry+')', 2500);
        //setup another ajaxmagic
        return;
    }
    $('#preloader').hide();
    $('#table-goes-here').append(report.data);
    buildTable($('#report-table'));
}

function buildTable(table) {
    table.dataTable({
        'bJQueryUI':true,
        'aLengthMenu': [[50,100,-1], [50, 100, 'All']],
        'iDisplayLength' : 50,
        'aoColumnDefs': [
            {
                'asSorting': ['desc', 'asc'],
                'aTargets': [0,1,2,3,4]
            }
        ],
        "aaSorting": [[ 1, 'asc' ]]
    });
}

$(document).ready(checkReport(retry));

/*
 * Tinycon - A small library for manipulating the Favicon
 * Tom Moor, http://tommoor.com
 * Copyright (c) 2012 Tom Moor
 * MIT Licensed
 * @version 0.1
*/

(function(){

	var Tinycon = {};
	var currentFavicon = null;
	var originalFavicon = null;
	var originalTitle = document.title;
	var faviconImage = null;
	var canvas = null;
	var options = {};
	var defaults = {
		width: 7,
		height: 9,
		font: '10px arial',
		colour: '#ffffff',
		background: '#F03D25',
		fallback: true
	};

	var ua = function(browser){
		var agent = navigator.userAgent.toLowerCase();
		return agent.indexOf(browser) !== -1;
	};

	var browser = {
		chrome: ua('chrome'),
		webkit: ua('chrome') || ua('safari'),
		safari: ua('safari') && !ua('chrome'),
		mozilla: ua('mozilla') && !ua('chrome') && !ua('safari')
	};

	// private
	var getFaviconTag = function(){

		var links = document.getElementsByTagName('link');

		for(var i=0; i < links.length; i++) {
			if (links[i].getAttribute('rel') === 'icon') {
				return links[i];
			}
		}

		return false;
	};

	var removeFaviconTag = function(){

		var links = document.getElementsByTagName('link');
		var head = document.getElementsByTagName('head')[0];

		for(var i=0; i < links.length; i++) {
			if (links[i].getAttribute('rel') === 'icon') {
				head.removeChild(links[i]);
			}
		}
	};

	var getCurrentFavicon = function(){

		if (!originalFavicon || !currentFavicon) {
			var tag = getFaviconTag();
			originalFavicon = currentFavicon = tag ? tag.getAttribute('href') : '/favicon.ico';
		}

		return currentFavicon;
	};

	var getCanvas = function (){

		if (!canvas) {
			canvas = document.createElement("canvas");
			canvas.width = 16;
			canvas.height = 16;
		}

		return canvas;
	};

	var setFaviconTag = function(url){
		removeFaviconTag();

		var link = document.createElement('link');
		link.type = 'image/x-icon';
		link.rel = 'icon';
		link.href = url;
		document.getElementsByTagName('head')[0].appendChild(link);
	};

	var log = function(message){
		if (window.console) window.console.log(message);
	};

	var drawFavicon = function(num, colour) {

		// fallback to updating the browser title if unsupported
		if (!getCanvas().getContext || (!browser.chrome && !browser.mozilla)) {
			return updateTitle(num);
		}

		var context = getCanvas().getContext("2d");
		var colour = colour || '#000000';
		var num = num || 0;

		faviconImage = new Image();
		faviconImage.onload = function() {

			// clear canvas
			context.clearRect(0, 0, 16, 16);

			// draw original favicon
			context.drawImage(faviconImage, 0, 0);

			// draw bubble over the top
			if (num > 0) drawBubble(context, num, colour);

			// refresh tag in page
			refreshFavicon();
		};

		faviconImage.src = getCurrentFavicon();
	};

	var updateTitle = function(num) {

		if (options.fallback) {
			if (num > 0) {
				document.title = '('+num+') ' + originalTitle;
			} else {
				document.title = originalTitle;
			}
		}
	};

	var drawBubble = function(context, num, colour) {

		// bubble needs to be larger for double digits
		var len = (num+"").length-1;
		var width = options.width + (6*len);
		var w = 16-width;
		var h = 16-options.height;

		// webkit seems to render fonts lighter than firefox
		context.font = (browser.webkit ? 'bold ' : '') + options.font;
		context.fillStyle = options.background;
		context.strokeStyle = options.background;
		context.lineWidth = 1;

		// bubble
		context.fillRect(w,h,width-1,options.height);

		// rounded left
		context.beginPath();
		context.moveTo(w-0.5,h+1);
		context.lineTo(w-0.5,15);
		context.stroke();

		// rounded right
		context.beginPath();
		context.moveTo(15.5,h+1);
		context.lineTo(15.5,15);
		context.stroke();

		// bottom shadow
		context.beginPath();
		context.strokeStyle = "rgba(0,0,0,0.3)";
		context.moveTo(w,16);
		context.lineTo(15,16);
		context.stroke();

		// number
		context.fillStyle = options.colour;
		context.textAlign = "right";
		context.textBaseline = "top";

		// unfortunately webkit/mozilla are a pixel different in text positioning
		context.fillText(num, 15, browser.webkit ? 6 : 7);
	};

	var refreshFavicon = function(){
		// check support
		if (!getCanvas().getContext) return;

		setFaviconTag(getCanvas().toDataURL());
	};


	// public
	Tinycon.setOptions = function(custom){
		options = {};

		for(var i in defaults){
			options[i] = custom[i] ? custom[i] : defaults[i];
		}
		return this;
	};

	Tinycon.setImage = function(url){
		currentFavicon = url;
		refreshFavicon();
		return this;
	};

	Tinycon.setBubble = function(num, colour){

		// validate
		if(isNaN(num)) return log('Bubble must be a number');

		drawFavicon(num, colour);
		return this;
	};

	Tinycon.reset = function(){
		Tinycon.setImage(originalFavicon);
	};

	Tinycon.setOptions(defaults);
	window.Tinycon = Tinycon;
})();
(function($){

    var config = window.ToastjsConfig = {
        defaultTimeOut: 3000,
        position: ["top", "right"],
        notificationStyles: {
            padding: "12px 18px",
            margin: "0 0 6px 0",
            backgroundColor: "#000",
            opacity: 0.8,
            color: "#fff",
            font: "normal 13px 'Droid Sans', sans-serif",
            borderRadius: "3px",
            boxShadow: "#999 0 0 12px",
            width: "300px"
        },
        notificationStylesHover: {
            opacity: 1,
            boxShadow: "#000 0 0 12px"
        },
        container: $("<div></div>")
    };

    $(document).ready(function() {
        config.container.css("position", "absolute");
        config.container.css("z-index", 9999);
        config.container.css(config.position[0], "12px");
        config.container.css(config.position[1], "12px");
        $("body").append(config.container);
    });

    function getNotificationElement() {
        return $("<div>").css(config.notificationStyles).hover(function() {
            $(this).css(config.notificationStylesHover);
        }, function() {
            $(this).css(config.notificationStyles);
        });
    }

    var Toast = window.Toast = {};

    Toast.notify = function(message, title, iconUrl, timeOut) {
        var notificationElement = getNotificationElement();

        timeOut = timeOut || config.defaultTimeOut;

        if (iconUrl) {
            var iconElement = $("<img/>", {
                src: iconUrl,
                css: {
                    width: 36,
                    height: 36,
                    display: "inline-block",
                    verticalAlign: "middle"
                }
            });
            notificationElement.append(iconElement);
        }

        var textElement = $("<div/>").css({
            display: 'inline-block',
            verticalAlign: 'middle',
            padding: '0 12px'
        });

        if (title) {
            var titleElement = $("<div/>");
            titleElement.append(document.createTextNode(title));
            titleElement.css("font-weight", "bold");
            textElement.append(titleElement);
        }

        if (message) {
            var messageElement = $("<div/>");
            messageElement.append(document.createTextNode(message));
            textElement.append(messageElement);
        }

        notificationElement.delay(timeOut).fadeOut(function(){
            notificationElement.remove();
        });
        notificationElement.bind("click", function() {
            notificationElement.hide();
        });

        notificationElement.append(textElement);
        config.container.prepend(notificationElement);
    };

    Toast.info = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.warning = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.error = function(message, title) {
        Toast.notify(message, title, "/images/36x36-error.png");
    };

    Toast.success = function(message, title) {
        Toast.notify(message, title, "/images/36x36-success.png");
    };

}(this.jQuery));
/*
 * jQuery Plugin: Tokenizing Autocomplete Text Entry
 * Version 1.1
 *
 * Copyright (c) 2009 James Smith (http://loopj.com)
 * Licensed jointly under the GPL and MIT licenses,
 * choose which one suits your project best!
 *
 */

(function($) {

$.fn.tokenInput = function (url, options) {
    var settings = $.extend({
        url: url,
        hintText: "Type in a search term",
        noResultsText: "No results",
        searchingText: "Searching...",
        searchDelay: 300,
        minChars: 1,
        tokenLimit: null,
        jsonContainer: null,
        method: "GET",
        contentType: "json",
        queryParam: "q",
        onResult: null,
        onAdd: null,
        onDelete: null,
        doImmediate:true,
        country:'US',
        featureClass: null,
        featureCode:null,
        maxRows: 10
   }, options);

    settings.classes = $.extend({
        tokenList: "token-input-list",
        token: "token-input-token",
        tokenDelete: "token-input-delete-token",
        selectedToken: "token-input-selected-token",
        highlightedToken: "token-input-highlighted-token",
        dropdown: "token-input-dropdown",
        dropdownItem: "token-input-dropdown-item",
        dropdownItem2: "token-input-dropdown-item2",
        selectedDropdownItem: "token-input-selected-dropdown-item",
        inputToken: "token-input-input-token"
    }, options.classes);

    return this.each(function () {
        var list = new $.TokenList(this, settings);
    });
};

$.TokenData = function(data,type) {
    var raw = data;
    var name;
    var input;
    var id;
    var code;
    function city_input() {
        var value = raw.lat + ',' + raw.lng + ':' + raw.adminCode1 + ':' + raw.name + ':' + raw.countryCode;
        return $('<input type="hidden" class="' + raw.countryCode + '" name="cities" id="' + raw.name.replace(/ /gi, '_') + '" value="' + value + '" />');
    }
    function country_input() {
        return $('<input type="hidden" name="geo" id="' + code + '" value="' + code + '" />');
    }

    if (type == 'city') {
        name = raw.name + ", " + raw.adminCode1;
        input = city_input;
        id = raw.name;
    }
    else if (type == 'country') {
        code = (raw.data === undefined) ? raw.code : raw.data.code;
        name = (raw.data === undefined) ? raw.name : raw.data.name;
        input = country_input;
        id = code;
    }


    return {
        name: name,
        input: input,
        raw: data,
        type: type,
        id: id
    };
}

$.TokenList = function (input, settings) {
    //
    // Variables
    //
    // Input box position "enum"
    var POSITION = {
        BEFORE: 0,
        AFTER: 1,
        END: 2
    };

    // Keys "enum"
    var KEY = {
        BACKSPACE: 8,
        TAB: 9,
        RETURN: 13,
        ESC: 27,
        LEFT: 37,
        UP: 38,
        RIGHT: 39,
        DOWN: 40,
        COMMA: 188
    };

    // Save the tokens
    var saved_tokens = [];

    // Keep track of the number of tokens in the list
    var token_count = 0;
    var token_id    = 0;

    // Basic cache to save on db hits
    var cache = new $.TokenList.Cache( settings );

    // Keep track of the timeout
    var timeout;

    // Create a new text input an attach keyup events
    var input_box = $("<input class=\"token-input-field\" type=\"text\"  autocomplete=\"off\">")
        .css({
            outline: "none"
        })
        .focus(function () {
            if (settings.tokenLimit === null || settings.tokenLimit != token_count) {
                show_dropdown_hint();
            }
            $(this).addClass('focused');
            if( !token_list.hasClass('focused')) {
                token_list.addClass('focused');
            }
            if( $(this).val() ) {
              setTimeout(function(){do_search(settings.doImmediate);}, 5);
           }
        })
        .blur(function () {
            $(this).removeClass('focused');
            token_list.removeClass('focused');
            hide_dropdown();
        })
        .keydown(function (event) {
            var previous_token;
            var next_token;

            switch(event.keyCode) {
                case KEY.LEFT:
                case KEY.RIGHT:
                case KEY.UP:
                case KEY.DOWN:
                    if(!$(this).val()) {
                        previous_token = input_token.prev();
                        next_token = input_token.next();

                        if((previous_token.length && previous_token.get(0) === selected_token) || (next_token.length && next_token.get(0) === selected_token)) {
                            // Check if there is a previous/next token and it is selected
                            if(event.keyCode == KEY.LEFT || event.keyCode == KEY.UP) {
                                deselect_token($(selected_token), POSITION.BEFORE);
                            } else {
                                deselect_token($(selected_token), POSITION.AFTER);
                            }
                        } else if((event.keyCode == KEY.LEFT || event.keyCode == KEY.UP) && previous_token.length) {
                            // We are moving left, select the previous token if it exists
                            select_token($(previous_token.get(0)));
                        } else if((event.keyCode == KEY.RIGHT || event.keyCode == KEY.DOWN) && next_token.length) {
                            // We are moving right, select the next token if it exists
                            select_token($(next_token.get(0)));
                        }
                    } else {
                        var dropdown_item = null;

                        if(event.keyCode == KEY.DOWN || event.keyCode == KEY.RIGHT) {
                            dropdown_item = $(selected_dropdown_item).next();
                        } else {
                            dropdown_item = $(selected_dropdown_item).prev();
                        }

                        if(dropdown_item.length) {
                            select_dropdown_item(dropdown_item);
                        }
                        return false;
                    }
                    break;

                case KEY.BACKSPACE:
                    previous_token = input_token.prev();

                    if(!$(this).val().length) {
                        if(selected_token) {
                            delete_token($(selected_token));
                        } else if(previous_token.length) {
                            select_token($(previous_token.get(0)));
                        }

                        return false;
                    } else if($(this).val().length == 1) {
                        hide_dropdown();
                    } else {
                        // set a timeout just long enough to let this function finish.
                        setTimeout(function(){do_search(settings.doImmediate);}, 5);
                   }
                    break;

                case KEY.TAB:
                case KEY.RETURN:
                case KEY.COMMA:
                  if(selected_dropdown_item) {
                    add_token($(selected_dropdown_item));
                    return false;
                  }
                  break;

                case KEY.ESC:
                  hide_dropdown();
                  return true;

                default:
                    if(is_printable_character(event.keyCode)) {
                      // set a timeout just long enough to let this function finish.
                      setTimeout(function(){do_search(settings.doImmediate);}, 5);
                    }
                    break;
            }
        });

    // Keep a reference to the original input box
    var hidden_input = $(input)
                           .hide()
                           .focus(function () {
                               input_box.focus();
                           })
                           .blur(function () {
                               input_box.blur();
                           });

    // Keep a reference to the selected token and dropdown item
    var selected_token = null;
    var selected_dropdown_item = null;

    // The list to store the token items in
    var token_list = $("<ul />")
        .addClass(settings.classes.tokenList)
        .insertBefore(hidden_input)
        .click(function (event) {
            $(this).addClass('focused');
            var li = get_element_from_event(event, "li");
            if(li && li.get(0) != input_token.get(0)) {
                toggle_select_token(li);
                return false;
            } else {
                input_box.focus();

                if(selected_token) {
                    deselect_token($(selected_token), POSITION.END);
                }
            }
        })
        .mouseover(function (event) {
            var li = get_element_from_event(event, "li");
            if(li && selected_token !== this) {
                li.addClass(settings.classes.highlightedToken);
            }
        })
        .mouseout(function (event) {
            var li = get_element_from_event(event, "li");
            if(li && selected_token !== this) {
                li.removeClass(settings.classes.highlightedToken);
            }
        })
        .mousedown(function (event) {
            // Stop user selecting text on tokens
            var li = get_element_from_event(event, "li");
            if(li){
                return false;
            }
        });


    // The list to store the dropdown items in
    var dropdown = $("<div>")
        .addClass(settings.classes.dropdown)
        .insertAfter(token_list)
        .hide();

    // The token holding the input box
    var input_token = $("<li />")
        .addClass(settings.classes.inputToken)
        .appendTo(token_list)
        .append(input_box);

    //
    //
    // Functions
    //


  //If more than two countries exist, select Everywhere, disable other options, and get rid of all of their inputs
  function verify_token_inputs() {
    var countries = $('.token-input-country').length;
    //more than one country
    if (countries > 1) {
        //delete all other tokens
        $('.token-input-city').each( function(i) {
           delete_token($(this));
        });
        $('.token-input-state').each( function(i) {
           delete_token($(this));
        });
        //disable everything else
        $('input[name="location-targeting"]').each(
            function(i) {
                if ($(this).val() != 'all') {
                    $(this).attr('disabled', true);
                }
                //Select "Everywhere"
                else {
                    $(this).click();
                }
        });
    }
    // turn all buttons back on
    else {
        $('input[name="location-targeting"]').each(
            function(i) {
                $(this).attr('disabled', false);
        });
    }

    // Only show countryNumDpdnt things that match the current number
    // of countries in the input
    var children = $('#geo_pred_ta').children().length;
    $('.countryNumDependent').hide();
    $('.countryNumDependent.' + children).show();

  }



    // Pre-populate list if items exist
    function init_list () {
        var li_data = settings.prePopulate.data;
        if(li_data && li_data.length) {
            for(var i in li_data) {
                var token_data = new $.TokenData(li_data[i], settings.prePopulate.type);
                var this_token = $("<li><p>"+ token_data.name+"</p> </li>")
                    .addClass(settings.classes.token);
                if (token_data.type == 'city') {
                    this_token.addClass('token-input-city')
                    .addClass(token_data.raw.countryCode);
                }
                else if (token_data.type == 'country') {
                    this_token.addClass('token-input-country');
                }
                    this_token.insertBefore(input_token);
                $("<span>&times;</span>")
                    .addClass(settings.classes.tokenDelete)
                    .appendTo(this_token)
                    .click(function () {
                        delete_token($(this).parent());
                        return false;
                    });
                $.data(this_token.get(0), "tokeninput", token_data);

                // Clear input box and make sure it keeps focus
                input_box
                    .val("")
                    .focus();

                // Don't show the help dropdown, they've got the idea
                hide_dropdown();

                // Save this token id
                token_data.input().appendTo( hidden_input );
            }
        }
        input_box.blur();
    }

    init_list();
    verify_token_inputs();

    function is_printable_character(keycode) {
        if((keycode >= 48 && keycode <= 90) ||      // 0-1a-z
           (keycode >= 96 && keycode <= 111) ||     // numpad 0-9 + - / * .
           (keycode >= 186 && keycode <= 192) ||    // ; = , - . / ^
           (keycode >= 219 && keycode <= 222)       // ( \ ) '
          ) {
              return true;
          } else {
              return false;
          }
    }

    // Get an element of a particular type from an event (click/mouseover etc)
    function get_element_from_event (event, element_type) {
        return $(event.target).closest(element_type);
    }

    // Inner function to a token to the list
    function insert_token(datas) {
      var value = datas.name;
      var token_type;
      var this_token = $("<li><p>"+ value +"</p> </li>");

      if (datas.type == 'city') {
          this_token.addClass('token-input-city')
          .addClass(datas.raw.countryCode);
      }/*
      else if (datas.type == 'state') {
          token_type = 'token-input-state';
      }*/
      else if (datas.type == 'country') {
          this_token.addClass('token-input-country');
      }
      this_token.addClass(settings.classes.token)
      .insertBefore(input_token);

      // The 'delete token' button
      $("<span>x</span>")
          .addClass(settings.classes.tokenDelete)
          .appendTo(this_token)
          .click(function () {
              delete_token($(this).parent());
              return false;
          });
      $.data(this_token.get(0), "tokeninput", datas);
      return this_token;
    }

    // Add a token to the token list based on user input
    function add_token(item) {
        //Make sure token stuff is okay before adding a new one
        verify_token_inputs();
        var li_data = $.data(item.get(0), "tokeninput");
        var this_token = insert_token(li_data);
        var callback = settings.onAdd;

        // Clear input box and make sure it keeps focus
        input_box
            .val("")
            .focus();

        // Don't show the help dropdown, they've got the idea
        hide_dropdown();

        //XXX IMPORTANT XXX
        //order for id_string should be:
        // [country], region], city]
        // so US is US, California is US,CA and San Francisco is US,CA,SF (or some something like that)
        // This is because the django forms are going to take this id, split it on ',' and then assign
        // the first value as country_name, 2nd as region_name, and 3rd as city_name
        li_data.input().appendTo(hidden_input);

        token_count++;
        //Strictly increasing number so we can name the hidden inputs
        token_id++;

        if(settings.tokenLimit !== null && token_count >= settings.tokenLimit) {
            input_box.hide();
            hide_dropdown();
        }

				// Execute the onAdd callback if defined
				if($.isFunction(callback)) {
				  callback(li_data.id);
				}
        //make sure token stuff is okay after adding a new one
        verify_token_inputs();
    }

    // Select a token in the token list
    function select_token (token) {
        token.addClass(settings.classes.selectedToken);
        selected_token = token.get(0);

        // Hide input box
        input_box.val("");

        // Hide dropdown if it is visible (eg if we clicked to select token)
        hide_dropdown();
    }

    // Deselect a token in the token list
    function deselect_token (token, position) {
        token.removeClass(settings.classes.selectedToken);
        selected_token = null;

        if(position == POSITION.BEFORE) {
            input_token.insertBefore(token);
        } else if(position == POSITION.AFTER) {
            input_token.insertAfter(token);
        } else {
            input_token.appendTo(token_list);
        }

        // Show the input box and give it focus again
        input_box.focus();
    }

    // Toggle selection of a token in the token list
    function toggle_select_token (token) {
        if(selected_token == token.get(0)) {
            deselect_token(token, POSITION.END);
        } else {
            if(selected_token) {
                deselect_token($(selected_token), POSITION.END);
            }
            select_token(token);
        }
    }

    // Delete a token from the token list
    function delete_token (token) {
        // Remove the id from the saved list
        var token_data = $.data(token.get(0), "tokeninput");
        var callback = settings.onDelete;
        // Delete the token
        token.remove();
        selected_token = null;
        //TODO delete the hidden field wooo
        // Show the input box and give it focus again
        input_box.focus();
        // Delete this token's id from hidden input
        if (token_data === undefined) {
            return;
        }
        var r_id = token_data.id.replace(/ /gi, '_');
        var r_nme = token_data.name.replace(/ /gi, '_');
        $('#'+ r_id).remove();
        $('#'+ r_nme).remove();

        if (token_data.type == 'country') {
            $('li.'+token_data.id+'.token-input-city').each( function(i) {
                    delete_token($(this));
                });
        }

        token_count--;

        if ($('.token-input-country').length === 0) {
            $('#advertiser-LocationSpec-all').click();
        }

        if (settings.tokenLimit !== null) {
            input_box
                .show()
                .val("")
                .focus();
        }


        // Execute the onDelete callback if defined
        if($.isFunction(callback)) {
          callback(token_data.id);
        }
        //verify inputs after token has been removed
        verify_token_inputs();
    }

    // Hide and clear the results dropdown
    function hide_dropdown () {
        dropdown.hide().empty();
        selected_dropdown_item = null;
    }

    function show_dropdown_searching () {
        dropdown
            .html("<p>"+settings.searchingText+"</p>")
            .show();
    }

    function show_dropdown_hint () {
        dropdown
            .html("<p>"+settings.hintText+"</p>")
            .show();
    }

    // Highlight the query part of the search term
	function highlight_term(value, term) {
        var ret_val = value.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + term + ")(?![^<>]*>)(?![^&;]+;)", "gi"), "<b>$1</b>");
		return ret_val;
	}

    var slide_state = false;
    // Populate the results dropdown with some results
    function populate_dropdown (query, results) {
        var type = results.type;
        results = results.data;
        if(results && results.length) {
            var drop_clone = dropdown.clone();
            drop_clone.empty();
            var dropdown_ul = $("<ul>")
                .appendTo(drop_clone)
                .mouseover(function (event) {
                    select_dropdown_item(get_element_from_event(event, "li"));
                })
                .mousedown(function (event) {
                    add_token(get_element_from_event(event, "li"));
                    return false;
                });
            if ( !slide_state ) {
                dropdown_ul.hide();
            }
            var name;
            for(var i in results) {
                if (results.hasOwnProperty(i)) {
                    var tokenData = new $.TokenData(results[i],type);
                    var this_li = $("<li>"+highlight_term(tokenData.name, query)+"</li>")
                                      .appendTo(dropdown_ul);
                    if(i%2) {
                        this_li.addClass(settings.classes.dropdownItem);
                    } else {
                        this_li.addClass(settings.classes.dropdownItem2);
                    }
                    //JSLint doesn't like this, but needs to be == because '0' == 0 evals to true, but '0' === 0 does NOT
                    if(i == 0) {
                        select_dropdown_item(this_li);
                    }
                    $.data(this_li.get(0), "tokeninput", tokenData);
                }
            }
            dropdown.replaceWith(drop_clone);
            dropdown = drop_clone;
            dropdown.show();
            if (!slide_state) {
                slide_state = true;
                dropdown_ul.slideDown("fast");
            }

        } else {
            slide_state = false;
            dropdown
                .html("<p>"+settings.noResultsText+"</p>")
                .show();
        }
    }

    // Highlight an item in the results dropdown
    function select_dropdown_item (item) {
        if(item) {
            if(selected_dropdown_item) {
                deselect_dropdown_item($(selected_dropdown_item));
            }

            item.addClass(settings.classes.selectedDropdownItem);
            selected_dropdown_item = item.get(0);
        }
    }

    // Remove highlighting from an item in the results dropdown
    function deselect_dropdown_item (item) {
        item.removeClass(settings.classes.selectedDropdownItem);
        selected_dropdown_item = null;
    }

    // Do a search and show the "searching" dropdown if the input is longer
    // than settings.minChars
    function do_search(immediate) {
        var query = input_box.val().toLowerCase();

        if (query && query.length) {
            if(selected_token) {
                deselect_token($(selected_token), POSITION.AFTER);
            }
            if (query.length >= settings.minChars) {
                show_dropdown_searching();
                if (immediate) {
                    run_search(query);
                } else {
                    clearTimeout(timeout);
                    timeout = setTimeout(function(){run_search(query);}, settings.searchDelay);
                }
            } else if (query.length > 0) {
                show_dropdown_hint();
            }
            else {
                hide_dropdown();
            }
        }
    }

    // Do the actual search
    function run_search(query) {
        //Don't run with the query given, run with what's actually in the search box
        query = input_box.val().toLowerCase();
        var cached_results = cache.get(query);
        if(cached_results) {
            var pop = {type:'country', data:cached_results};
            populate_dropdown(query, pop);
        } else {
			var queryStringDelimiter = settings.url.indexOf("?") < 0 ? "?" : "&";
			var callback = function(results) {
			  if($.isFunction(settings.onResult)) {
			      results = settings.onResult.call(this, results);
			  }
              cache.add(query, settings.jsonContainer ? results[settings.jsonContainer] : results);
              var pop = {type: settings.type, data:results.geonames};
              populate_dropdown(query, pop);
            };

            if(settings.method == "POST") {
			    $.post(settings.url + queryStringDelimiter + settings.queryParam + "=" + encodeURIComponent(query), {}, callback, settings.contentType);
		    } else {
                var q_url = settings.url + queryStringDelimiter + settings.queryParam + "=" + encodeURIComponent(query);
                if (settings.featureClass !== null) {
                    q_url += '&featureClass=' + encodeURIComponent(settings.featureClass);
                }
                if (settings.featureCode !== null) {
                    q_url += "&featureCode=" + encodeURIComponent(settings.featureCode);
                }
                q_url += '&country=';
                if ($('input[name="geo"]').val() !== undefined) {
                   q_url += encodeURIComponent($('input[name="geo"]').val());
                }
                else {
                    q_url += encodeURIComponent(settings.country);
                }
                q_url += '&maxRows=' + settings.maxRows;
		        $.get(q_url, {}, callback, settings.contentType);
		    }
       }
    }
};

// Really basic cache for the results
$.TokenList.Cache = function (options) {
    var settings = $.extend({
        max_size: 50,
        matchContains: true
    }, options);

    function matchSubset( s, sub ) {
        if ( !options.matchCase ) {
            s = s.toLowerCase();
        }
        var i = s.indexOf( sub );
        if ( i == -1 ) {
            return false;
        }
        return i === 0 || options.matchContains;
    }


    var data = {};
    var size = 0;

    var flush = function () {
        data = {};
        size = 0;
    };

    function res_sort( query ) {
        function actual_sort( a, b ) {
            return q_dist( query, a.value ) - q_dist( query, b.value );
        }
        return actual_sort;
    }

    function q_dist( query, value ) {
        return value.length - query.length;
    }


    function get(q) {
        if (!options.cacheLength || !size) {
            return null;
        }
        if ( !options.url && settings.matchContains ){
           var csub = [];
           for ( var k in data ) {
               if( k.length > 0 ) {
                   var c = data[k];
                   $.each( c, function( i, x ) {
                      if (matchSubset( x.value, q ) ) {
                          var add = true;
                          for( var idx in csub ) {
                              var dat = csub[idx];
                              if ( x.result == dat.result ) {
                                  add = false;
                                  break;
                              }
                          }
                          if (add) {
                            csub.push(x);
                            }
                        }
                    });
               }
           }
           return csub.sort(res_sort(q));
        }
        else if( data[q] ) {
            return data[q];
        }
        else if (settings.matchSubset) {
            for (var i = q.length - 1; i >= 1; i--) {
                var c = data[ q.substr( 0, i ) ];
                if (c) {
                    var csub = [];
                    $.each( c, function( i, x ) {
                        if( matchSubset( x.value, q ) ){
                            csub[csub.length] = x;
                        }
                    });
                    return csub;
                }
            }
        }
        return null;
    }

    function populate() {
        if (!options.data ) {return false;}
        var stMatchSets = {},
            nullData = 0;

        if (!options.url) {options.cacheLength = 1;}

        stMatchSets[""] = [];

        for (var i = 0, ol = options.data.length; i < ol; i++ ) {
            var rawValue = options.data[i];
            rawValue = (typeof rawValue == "string" ) ? [rawValue] : rawValue;

            var values = options.formatMatch( rawValue, i+1, options.data.length );
            for (var j = 0; j < values.length; j++) {
                var value = values[j];
                if (value === false)
                    {continue;}
                var firstChar = value.charAt( 0 ).toLowerCase();
                if (!stMatchSets[ firstChar ] )
                    {stMatchSets[ firstChar ] = [];}
                var row = {
                     value: value,
                     data: rawValue,
                     result: options.formatResult && options.formatResult( rawValue ) || value
                 };
                 stMatchSets[ firstChar ].push( row );
                 if ( nullData++ < options.max ) {
                     stMatchSets[""].push( row );
                 }
            }
        }
        $.each( stMatchSets, function( i, value ) {
            options.cacheLength++;
            add( i, value );
        });
    }
    setTimeout(populate, 25);




    function add(query, results) {
        if(size > settings.max_size) {
            flush();
        }

        if(!data[query]) {
            size++;
        }
        data[query] = results;
    }

    return {
        flush: flush,
        get: get,
        populate: populate,
        add: add
    };


//    this.get = function (query) {
//        return data[query];
//    };
};

})(jQuery);
(function($, Backbone, _) {

    /*
     * ## AccountRollUp
     * This model holds the rolled up ad network reporting data for an account
     */
    var AccountRollUp = Backbone.Model.extend({
        defaults : {
            revenue: 0,
            attempts: 0,
            impressions: 0,
            cpm: 0,
            fill_rate: 0,
            clicks: 0,
            cpc: 0,
            ctr: 0,
        },
        url: function () {
            return '/api/ad_network/account_roll_up/'
        },
    });

    /*
     * ## DailyStatsCollection
     * Holds the stats to render the chart.
     */
    var DailyStatsCollection = Backbone.Collection.extend({
        model: AppOnNetwork,
        url: function () {
            return '/api/ad_network/daily_stats/'
        },
    });

    /*
     * ## RollUp
     * This model holds the ad network reporting data for either an application
     * or an ad network.
     */
    var RollUp = Backbone.Model.extend({
        defaults : {
            revenue: 0,
            attempts: 0,
            impressions: 0,
            cpm: 0,
            fill_rate: 0,
            clicks: 0,
            cpc: 0,
            ctr: 0,
        },
        url: function () {
            return '/api/ad_network/roll_up/'
                + this.get('type')
                + '/id/'
                + this.id
        },
    });

    /*
     * ## AppOnNetwork
     * This model holds the ad network reporting data for an application on a a specific network.
     */
    var AppOnNetwork = Backbone.Model.extend({
        defaults : {
            name: '',
            revenue: 0,
            attempts: 0,
            impressions: 0,
            cpm: 0,
            fill_rate: 0,
            clicks: 0,
            cpc: 0,
            ctr: 0,
        },
        url: function () {
            return '/api/ad_network/app_on_network/'
                + this.get('network')
                + '/pub_id/'
                + this.id;
        },
    });

    /*
     * ## AppOnNetworkCollection
     */
    var AppOnNetworkCollection = Backbone.Collection.extend({
        model: AppOnNetwork,
    });

    window.AccountRollUp = AccountRollUp;
    window.DailyStatsCollection = DailyStatsCollection;
    window.RollUp = RollUp;
    window.AppOnNetwork = AppOnNetwork;
    window.AppOnNetworkCollection = AppOnNetworkCollection;


})(this.jQuery, this.Backbone, this._);

/*
 * # models.js
 *
 * Backbone models
 */

/*jslint browser:true,
  fragment: true,
  maxlen: 110,
  nomen: true,
  indent: 4,
  vars: true,
  white: true
 */

var mopub = mopub || {};

(function ($, Backbone, _) {
    "use strict";

    /*
     * ## Campaigns
     */
    var Campaign = Backbone.Model.extend({
        defaults: {
            name: '',
            budget: 0.0,
            budget_type: '',
            start_datetime: new Date(),
            end_datetime: null,
            active: false
        }
    });

    /*
     * ## AdGroups
     */

    /*
     * Helper functions for stats
     */
    function calculate_ctr(impression_count, click_count) {
        if (impression_count === null || click_count === null) {
            return null;
        }
        return (impression_count === 0) ? 0 : click_count / impression_count;
    }

    function calculate_fill_rate(request_count, impression_count) {
        if (request_count === null || impression_count === null) {
            return null;
        }
        return (request_count === 0) ? 0 : impression_count / request_count;
    }

    function format_stat(stat, value) {
        if (value === null) {
            return '--';
        }
        switch (stat) {
          case 'click_count':
          case 'conversion_count':
          case 'goal':
          case 'impression_count':
          case 'request_count':
            return mopub.Utils.formatNumberWithCommas(value);
          case 'cpm':
          case 'revenue':
            return '$' + mopub.Utils.formatNumberWithCommas(value.toFixed(2));
          case 'conv_rate':
          case 'ctr':
          case 'fill_rate':
            return mopub.Utils.formatNumberAsPercentage(value);
          case 'status':
            return value;
        default:
            throw 'Unsupported stat "' + stat + '".';
        }
    }

    var ModelHelpers = {
        calculate_ctr: calculate_ctr,
        calculate_fill_rate: calculate_fill_rate,
        format_stat: format_stat
    };

    /*
     * ## AdGroup model
     * This will most likely need to be refactored soon when we change how
     * AdGroups work on the backend.
     */

    var AdGroup = Backbone.Model.extend({
        get_stat: function(stat) {
            if (!this.has(stat)) {
                return null;
            }
            return this.get(stat);
        },

        get_formatted_stat: function(stat) {
            return format_stat(stat, this.get_stat(stat));
        },

        get_stat_for_day: function(stat, day) {
            if (!this.has("daily_stats")) {
                return null;
            }
            var daily_stats = this.get("daily_stats");
            if (day >= daily_stats.length) {
                return null;
            }
            var day_stats = daily_stats[day];
            if (!stat in day_stats) {
                return null;
            }
            return day_stats[stat];
        },

        url: function() {
            return '/api/adgroup/' + this.id;
        }
    });


    /*
     * ## Adgroup Collection
     */
    var AdGroups = Backbone.Collection.extend({
        model: AdGroup,

        get_stat_sum: function(stat) {
            return this.reduce(function(memo, adgroup) {
                if (memo === null || !adgroup.has(stat)) {
                    return null;
                }
                return memo + adgroup.get(stat);
            }, 0);
        },

        get_stat: function(stat) {
            switch(stat) {
                case 'ctr':
                    return calculate_ctr(this.get_stat('impression_count'),
                                         this.get_stat('click_count'));
                case 'fill_rate':
                    return calculate_fill_rate(this.get_stat('request_count'),
                                               this.get_stat('impression_count'));
                case 'click_count':
                case 'conversion_count':
                case 'impression_count':
                case 'request_count':
                case 'revenue':
                    return this.get_stat_sum(stat);
                default:
                    throw 'Unsupported stat "' + stat + '".';
            }
        },

        get_formatted_stat: function(stat) {
            return format_stat(stat, this.get_stat(stat));
        },

        get_stat_sum_for_day: function(stat, day) {
            return this.reduce(function(memo, adgroup) {
                if (memo === null ||
                    !adgroup.has('daily_stats') ||
                    day >= adgroup.get('daily_stats').length ||
                    !(stat in adgroup.get('daily_stats')[day])) {
                    return null;
                }

                return memo + adgroup.get('daily_stats')[day][stat];
            }, 0);
        },

        get_stat_for_day: function(stat, day) {
            switch(stat) {
                case 'ctr':
                    return calculate_ctr(this.get_stat_for_day('impression_count', day),
                                         this.get_stat_for_day('click_count', day));
                case 'fill_rate':
                    return calculate_fill_rate(this.get_stat_for_day('request_count', day),
                                               this.get_stat_for_day('impression_count', day));
                case 'click_count':
                case 'conversion_count':
                case 'impression_count':
                case 'request_count':
                case 'revenue':
                    return this.get_stat_sum_for_day(stat, day);
                default:
                    throw 'Unsupported stat "' + stat + '".';
            }
        },

        get_formatted_stat_for_day: function(stat, day) {
            return format_stat(stat, this.get_stat_for_day(stat, day));
        },

        get_total_daily_stats: function(stat) {
            var total_daily_stats = [];
            var day;
            for(day in this.at(0).get('daily_stats')) {
                total_daily_stats.push(this.get_stat_for_day(stat, day));
            }
            return total_daily_stats;
        },

        get_chart_data: function(stat) {
            var adgroups = this.filter(function(adgroup) {
                return adgroup.has(stat) && adgroup.has('daily_stats');
            });
            if (adgroups.length === 0) {
                return [];
            }
            var sorted_adgroups = _.sortBy(adgroups, function(adgroup) {
                // dash because we're sorting in reverse order
                return -adgroup.get('impression_count');
            });
            var top_three_adgroups = sorted_adgroups.splice(0, 3);
            var other_adgroups = new AdGroups(sorted_adgroups);
            var chart_data = top_three_adgroups.map(function(adgroup) {
                var adgroup_data = {};
                adgroup_data[adgroup.get('name')] = _.map(adgroup.get('daily_stats'), function(day) {
                    return day[stat];
                });
                return adgroup_data;
            });
            if (other_adgroups.size()) {
                chart_data.push({
                    'Others': other_adgroups.get_total_daily_stats(stat)
                });
            }
            if (stat === 'ctr') {
                chart_data.push({
                    'MoPub Optimized': this.get_total_daily_stats('ctr')
                });
            }
            return chart_data;
        },

        get_days: function() {
            // TODO: make this less hacky
            return this.reduce(function(memo, adgroup) {
                return (adgroup.has('daily_stats') &&
                        adgroup.get('daily_stats').length > memo) ? adgroup.get('daily_stats').length : memo;
            }, 0);
        },

        isFullyLoaded: function() {
            // TODO: make this less hacky
            return this.reduce(function(memo, adgroup) {
                return memo && adgroup.has('impression_count');
            }, true);
        }
    });


    /*
     * ## AdUnit
     */
    var AdUnit = Backbone.Model.extend({
        // If we don't set defaults, the templates will explode
        defaults : {
            active: false,
            attempts: 0,
            clicks: 0,
            ctr: 0,
            ecpm: 0,
            fill_rate: 0,
            impressions: 0,
            name: '',
            price_floor: 0,
            requests: 0,
            revenue: 0,
            stats_endpoint: 'all'
        },
        validate: function(attributes) {
            if (typeof(attributes.price_floor) !== 'undefined') {
                var valid_number = Number(attributes.price_floor);
                if (isNaN(valid_number)) {
                    return "Please enter a valid number for the price floor";
                }
            }
        },
        url: function() {
            // window.location.search.substring(1) is used to preserve date ranges from the url
            // this makes the fetching work with the datepicker.
            var stats_endpoint = this.get('stats_endpoint');
            return '/api/app/'
                + this.app_id
                + '/adunits/'
                + this.id
                + '?'
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        }
    });

    /*
     * ## AdUnitCollection
     *
     * Should collections be named 'collection' or should we pluralize their
     * model name?
     */
    var AdUnitCollection = Backbone.Collection.extend({
        model: AdUnit,
        url: function() {
            // window.location.search.substring(1) is used to preserve date ranges from the url
            // this makes the fetching work with the datepicker.
            var stats_endpoint = this.stats_endpoint;
            return '/api/app/'
                + this.app_id
                + '/adunits/'
                + '?'
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        }
    });


    /*
     * ## App
     * We might consider turning derivative values (ecpm, fill_rate, ctr) into
     * functions.
     */
    var App = Backbone.Model.extend({
        defaults : {
            name: '',
            url:'#',
            icon_url: "/placeholders/image.gif",
            app_type: '',
            active: false,
            attempts: 0,
            clicks: 0,
            ctr: 0,
            ecpm: 0,
            fill_rate: 0,
            impressions: 0,
            price_floor: 0,
            requests: 0,
            revenue: 0,
            stats_endpoint: 'all'
        },
        url: function () {
            var stats_endpoint = this.get('stats_endpoint');
            return '/api/app/'
                + this.id
                + "?"
                + window.location.search.substring(1)
                + '&endpoint='
                + stats_endpoint;
        },
        parse: function (response) {
            // The api returns everything from this url as a list,
            // so that you can request one or all apps.
            var app = response[0];

            if (app.app_type === 'iphone') {
                app.app_type = 'iOS';
            }
            if (app.app_type === 'android') {
                app.app_type = 'Android';
            }
            if (app.app_type === 'mweb') {
                app.app_type = 'Mobile Web';
            }
            return app;
        },
        get_summed: function (attr) {
            if (typeof(this.get(attr)) !== 'undefined') {
                var series = this.get(attr);
                var sum = _.reduce(series, function(memo, num){
                    return memo + num;
                }, 0);
                return sum;
            }
            return null;
        }
    });

    /*
     * ## AppCollection
     */
    var AppCollection = Backbone.Collection.extend({
        model: App,
        // If an app key isn't passed to the url, it'll return a list
        // of all of the apps for the account
        url: function() {
            var stats_endpoint = this.stats_endpoint;
            return '/api/app/' +
                '?' + window.location.search.substring(1) +
                '&endpoint=' + stats_endpoint;
        },
        // Not used anymore, but could come in handy
        fetchAdUnits: function() {
            this.each(function (app) {
                app.adunits = new AdUnitCollection();
                app.adunits.app_id = app.id;
                app.adunits.fetch();
            });
        }
    });


    /*
     * EXPOSE HIS JUNK
     * (We should find a better way to do this.)
     */
    window.AdUnit = AdUnit;
    window.AdUnitCollection = AdUnitCollection;
    window.App = App;
    window.AppCollection = AppCollection;
    window.AdGroup = AdGroup;
    window.AdGroups = AdGroups;
    window.ModelHelpers = ModelHelpers;

}(this.jQuery, this.Backbone, this._));
(function($, Backbone) {

    /*
     * ## AccountRollUpView
     *
     */
    var AccountRollUpView = Backbone.View.extend({

        initialize: function () {
            this.model.bind('change', this.render, this);
        },

        render: function () {
            var stats_div = "#dashboard-stats .stats-breakdown";
            var inner = ".stats-breakdown-value .inner";
            $("#stats-breakdown-revenue " + inner, stats_div).text(mopub.Utils.formatCurrency(this.model.get("revenue")));
            $("#stats-breakdown-impressions " + inner, stats_div).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $("#stats-breakdown-clicks " + inner, stats_div).html('<span class="muted unbold">(' + mopub.Utils.formatNumberWithCommas(this.model.get("clicks")) + ')</span> ' + mopub.Utils.formatNumberAsPercentage(this.model.get("ctr")));

            return this;
        },
    });

    /*
     * ## DailyStatsView
     *
     * View for rendering the chart out of the daily stats.
     */
    var DailyStatsView = Backbone.View.extend({

        initialize: function () {
            this.collection.bind('reset', this.render, this);
        },

        render: function () {
            models = this.collection.models;
            var daily_stats = models.map(function(model) {
                  return model.attributes;
            });
            populateGraphWithStats(daily_stats);

            return this;
        },
    });

    /*
     * ## RollUpView
     *
     */
    var RollUpView = Backbone.View.extend({

        initialize: function () {
            this.model.bind('change', this.render, this);
        },

        render: function () {
            if(this.model.get("type") == 'network' && this.model.get("sync_date")) {
                $("#" + this.model.id + "-row .network-status span:first").append(this.model.get("sync_date"));
            }

            var mapper_row = $("tr#" + this.model.id + "-row");
            $(".revenue", mapper_row).text(mopub.Utils.formatCurrency(this.model.get("revenue")));
            $(".attempts", mapper_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("attempts")));
            $(".impressions", mapper_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("impressions")));
            $(".cpm", mapper_row).text(mopub.Utils.formatCurrency(this.model.get("cpm")));
            $(".fill-rate", mapper_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get("fill_rate")));
            $(".clicks", mapper_row).text(mopub.Utils.formatNumberWithCommas(this.model.get("clicks")));
            $(".cpc", mapper_row).text(mopub.Utils.formatCurrency(this.model.get("cpc")));
            $(".ctr", mapper_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get("ctr")));

            return this;
        },
    });

    /*
     * ## AppOnNetworkView
     *
     * See common/templates/partials/app_on_network.html to see how this is rendered in HTML.
     * This renders an app on a network as a table row.
     */
    var AppOnNetworkView = Backbone.View.extend({

        initialize: function () {
            this.model.bind('change', this.render, this);
        },

        render: function () {
            context_dict = {
                name: this.model.get('app_name') + '  ',
                network: this.model.get('network_name'),
                key: this.model.get('mapper_key'),
                url: '/ad_network_reports/app_view/' + this.model.get('mapper_key'),
                revenue: mopub.Utils.formatCurrency(this.model.get('revenue')),
                attempts: mopub.Utils.formatNumberWithCommas(this.model.get('attempts')),
                impressions: mopub.Utils.formatNumberWithCommas(this.model.get('impressions')),
                cpm: mopub.Utils.formatCurrency(this.model.get('cpm')),
                fill_rate: mopub.Utils.formatNumberAsPercentage(this.model.get('fill_rate')),
                clicks: mopub.Utils.formatNumberWithCommas(this.model.get('clicks')),
                cpc: mopub.Utils.formatCurrency(this.model.get('cpc')),
                ctr: mopub.Utils.formatNumberAsPercentage(this.model.get('ctr')),
            }
            network_html = _.template($('#app-on-network-row-template').html(), context_dict);

            $('#app-on-' + this.model.get('network')).append(network_html);

            // It will always insert in alphabetical order since we pull stats
            // from the networks in alphabetical order
            context_dict['name'] = this.model.get('network_name') + '  '
            app_html = _.template($('#app-on-network-row-template').html(), context_dict);
            $('#' + this.model.get('app_key') + '-on-networks').append(app_html);

            $('.details-row').mouseover(function () {
                var key = $(this).attr('id');
                $('.details-' + key).removeClass('hidden');
            });

            $('.details-row').mouseout(function () {
                var key = $(this).attr('id');
                $('.details-' + key).addClass('hidden');
            });

            return this;
        },
    });

    window.AccountRollUpView = AccountRollUpView;
    window.DailyStatsView = DailyStatsView;
    window.AppOnNetworkView = AppOnNetworkView;
    window.RollUpView = RollUpView;

})(this.jQuery, this.Backbone);

/*
 * # views.js
 * Reusable UI elements written with Backbone.
 */

/*jslint browser:true,
  fragment: true,
  maxlen: 110,
  nomen: true,
  indent: 4,
  vars: true,
  white: true
 */

var mopub = window.mopub || {};

(function ($, Backbone, _) {
    "use strict";
    /*
     * ## AdGroupsView
     * Parameters:
     * * collection: AdGroups
     * * el: element that will hold the content
     * * title: title that will be an h2 at the top of the content
     * * type: 'network', 'gtee', 'promo', or 'backfill_promo' -- affects which fields are shown
     * * tables: mapping of... MAPPING OF WHAT? I'M DYING TO KNOW
     */
    var AdGroupsView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },
        filtered_collection: function () {
            // TODO: uses elements not in this view
            var status = $('#campaigns-filterOptions').find(':checked').val();
            var app = $('#campaigns-appFilterOptions').val();
            return new AdGroups(this.collection.reject(function (adgroup) {
                return (status && status !== adgroup.get('status')) ||
                       (app && adgroup.get('apps').indexOf(app) === -1);
            }));
        },
        render: function () {
            var adgroups = this.filtered_collection();

            // TODO: uses elements not in this view, with multiple views there are conflicts

            var html;
            if (adgroups.size() === 0) {
                html = '<h2>No ' + this.options.title + '</h2>';
            } else {
                html = _.template($('#adgroups-rollup-template').html(), {
                    adgroups: adgroups,
                    title: this.options.title,
                    type: this.options.type
                });

                if (this.options.tables) {
                    var type = this.options.type;
                    _.each(this.options.tables, function (filter, title) {
                        var filtered_adgroups = new AdGroups(adgroups.filter(filter));
                        if(filtered_adgroups.length) {
                            html += _.template($('#adgroups-table-template').html(), {
                                adgroups: filtered_adgroups,
                                title: title,
                                type: type
                            });
                        }
                    });
                } else {
                    html += _.template($('#adgroups-table-template').html(), {
                        adgroups: adgroups,
                        title: 'Name',
                        type: this.options.type
                    });
                }
            }
            $(this.el).html(html);
            return this;
        }
    });


    /*
     * # CollectionGraphView
     * Renders a collection as a graph
     */

    var CollectionGraphView = Backbone.View.extend({
        initialize: function () {
            this.collection.bind('change', this.render, this);
        },

        show_chart: function () {
            if(this.collection.isFullyLoaded()) {
                var active_chart = $('#dashboard-stats .stats-breakdown .active');
                var use_ctr = active_chart.attr('id') === 'stats-breakdown-ctr';
                mopub.Chart.setupDashboardStatsChart(use_ctr ? 'line' : 'area');
            }
        },

        render: function () {
            var this_view = this;
            if (this_view.collection.isFullyLoaded()) {

                var metrics = ['impression_count', 'revenue', 'click_count', 'ctr'];

                // Render the stats breakdown for "all""
                $.each(metrics, function (iter, metric) {
                    var selector = '#stats-breakdown-' + metric + ' .all .inner';
                    $(selector).html(this_view.collection.get_formatted_stat(metric));
                });

                if (this_view.options.yesterday !== null && this_view.options.today !== null) {

                    // Render the stats breakdown for yesterday
                    $.each(metrics, function (iter, metric) {
                        var selector = '#stats-breakdown-' + metric + ' .yesterday .inner';
                        $(selector).html(this_view.collection.get_formatted_stat_for_day(metric,
                                         this_view.options.yesterday));
                    });

                    // Render the stats breakdown for yesterday
                    $.each(metrics, function (iter, metric) {
                        var selector = '#stats-breakdown-' + metric + ' .today .inner';
                        $(selector).html(this_view.collection.get_formatted_stat_for_day(metric,
                                         this_view.options.today));
                    });
                }

                // Chart
                mopub.dashboardStatsChartData = {
                    pointStart: this_view.options.start_date,
                    pointInterval: 86400000,
                    impression_count: this_view.collection.get_chart_data('impression_count'),
                    revenue: this_view.collection.get_chart_data('revenue'),
                    click_count: this_view.collection.get_chart_data('click_count'),
                    ctr: this_view.collection.get_chart_data('ctr')
                };
                this_view.show_chart();
            }
        }
    });

    /*
     * ## AppView
     *
     * See common/templates/partials/app.html to see how this is rendered in HTML.
     * This renders an app as a table row. It also adds the call to load
     * adunits over ajax and put them in the table.
     */
    var AppView = Backbone.View.extend({
        initialize: function () {
            try {
                this.template = _.template($('#app-template').html());
            } catch (e) {
                // the template wasn't specified. this is ok if you
                // intend to renderInline
            }
        },

        renderInline: function () {
            /*jslint maxlen: 200 */
            var app_row = $('tr.app-row#app-' + this.model.id, this.el);
            $('.revenue', app_row).text(mopub.Utils.formatCurrency(this.model.get('revenue')));
            $('.impressions', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('impressions')));
            $('.ecpm', app_row).text(mopub.Utils.formatCurrency(this.model.get('ecpm')));
            $('.clicks', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('clicks')));
            $('.ctr', app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('ctr')));
            $('.fill_rate', app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('fill_rate')));
            $('.requests', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.attempts', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.conversions', app_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('conversions')));
            $('.conv_rate', app_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('conversion_rate')));
            /*jslint maxlen: 110 */

            $(".loading-img", app_row).hide();

            return this;
        },
        render: function () {
            var renderedContent = $(this.template(this.model.toJSON()));

            // When we render an appview, we also attach a handler to fetch
            // and render it's adunits when a link is clicked.
            $('tbody', this.el).append(renderedContent);
            return this;
        }
    });

    /*
     * ## AdUnitView
     *
     * See common/templates/partials/adunit.html to see how this is rendered in HTML
     * Renders an adunit as a row in a table. Also ads the event handler to
     * submit the price floor change over ajax when the price_floor field is changed.
     */
    var AdUnitView = Backbone.View.extend({
        initialize: function () {
            try {
                this.template = _.template($('#adunit-template').html());
            } catch (e) {
                // you load the template partial in the page. ok if
                // you intend to renderInline.
            }
        },

        /*
         * Render the AdUnit into a table row that already exists. Adds handlers
         * for changing AdUnit attributes over ajax.
         */
        renderInline: function () {
            /*jslint maxlen: 200 */
            var current_model = this.model;
            var adunit_row = $('tr.adunit-row#adunit-' + this.model.id, this.el);
            $('.revenue', adunit_row).text(mopub.Utils.formatCurrency(this.model.get('revenue')));
            $('.ecpm', adunit_row).text(mopub.Utils.formatCurrency(this.model.get('ecpm')));
            $('.impressions', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('impressions')));
            $('.price_floor', adunit_row).html('<img class="loading-img hidden" ' +
                                               'src="/images/icons-custom/spinner-12.gif">' +
                                               '</img> ' +
                                               '<input id="' + this.model.id + '" ' +
                                               'type="text" ' +
                                               'class="input-text input-text-number number" ' +
                                               'style="width:50px;margin: -3px 0;" ' +
                                               'value="' + this.model.get('price_floor') +
                                               '"> ');
            $('.targeting', adunit_row).html('<img class="loading-img hidden" ' +
                                             'src="/images/icons-custom/spinner-12.gif"></img> ' +
                                             '<input class="targeting-box" type="checkbox">');

            $('.fill_rate', adunit_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('fill_rate')));
            $('.ctr', adunit_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('ctr')));
            $('.clicks', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('clicks')));
            $('.requests', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.attempts', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('requests')));
            $('.conversions', adunit_row).text(mopub.Utils.formatNumberWithCommas(this.model.get('conversions')));
            $('.conv_rate', adunit_row).text(mopub.Utils.formatNumberAsPercentage(this.model.get('conversion_rate')));
            /*jslint maxlen: 110 */

            if (this.model.get('active')) {
                $('input.targeting-box', adunit_row).attr('checked', 'checked');
            }

            // Add the event handler to submit targeting changes over ajax.
            $('input.targeting-box', adunit_row).click(function () {
                var loading_img = $('.targeting .loading-img', adunit_row);
                loading_img.show();
                current_model.save({'active': $(this).is(':checked')}, {
                    success: function () {
                        setTimeout(function () {
                            loading_img.hide();
                        }, 2000);
                    }
                });
            });

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor .input-text', adunit_row).keyup(function () {
                var input_field = $(this);
                input_field.removeClass('error');
                var loading_img = $(".price_floor .loading-img", adunit_row);
                loading_img.show();

                var promise = current_model.save({
                    price_floor: $(this).val()
                });
                if (promise) {
                    promise.success(function () {
                        loading_img.hide();
                    });
                    promise.error(function () {
                        loading_img.hide();
                    });
                } else {
                    loading_img.hide();
                    input_field.addClass('error');
                }
            });


            return this;
        },

        /*
         * Render the adunit model in the template. This assumes that the table
         * row for the app has already been rendered. This will render underneath
         * it's app's row.
         */
        render: function () {
            // render the adunit and attach it to the table after it's adunit's row
            var current_model = this.model;
            var renderedContent = $(this.template(this.model.toJSON()));

            // Add the event handler to submit price floor changes over ajax.
            $('.price_floor_change', renderedContent)
                .change(function () {
                    current_model.set({'price_floor': $(this).val()});
                    // Save when they click the save button in the price floor cell
                    var save_link = $('.save', $(this).parent());
                    save_link.click(function (e) {
                        e.preventDefault();
                        save_link.addClass('disabled').text('Saving...');
                        current_model.save({}, {
                            success: function () {
                                setTimeout(function () {
                                    save_link.removeClass('disabled').text('Saved');
                                    save_link.text('Save');
                                }, 2000);
                            }
                        });
                    });
                });

            // Add the event handler to submit targeting changes over ajax.
            $('input.targeting-box', renderedContent).click(function () {
                var targeting = $(this).attr('name');
                var activation = $(this).is(':checked') ? 'On' : 'Off';
                $('label[for="' + targeting + '"]', renderedContent).text(activation);

                current_model.set({'active': $(this).is(':checked')});
                current_model.save();
            });

            // Add the right background color based on where the app is in the table
            var app_row = $('tr#app-' + this.model.get('app_id'), this.el);
            var zebra = app_row.hasClass('even') ? 'even' : 'odd';
            renderedContent.addClass(zebra);

            app_row.after(renderedContent);

            return this;
        }
    });

    window.AdUnitView = AdUnitView;
    window.AppView = AppView;
    window.AdGroupsView = AdGroupsView;
    window.CollectionGraphView = CollectionGraphView;

}(this.jQuery, this.Backbone, this._));

/*
	MoPub Dashboard JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {

		// Hack to add the correct class to input fields
		$('input:text').addClass('input-text');
	    $('input:password').addClass('input-text');


		$(".button.continue")
    		.button({
    			icons: { secondary: "ui-icon-circle-triangle-e" }
    		})


		// Submit button
		$('#accountForm-submit')
			.button({
				icons: { secondary: "ui-icon-circle-triangle-e" }
			})
			.click(function(e) {
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
				container.togglebutton.button('option', {icons: { primary: 'ui-icon-triangle-1-n' }});
				setButtonTextElement(container.togglebutton, container.togglebutton.hideText);
			}

			function didHideContainer(container) {
				container.removeClass('show');
				container.addClass('hide');
				container.togglebutton.button('option', {icons: { primary: 'ui-icon-triangle-1-s' }});
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

			infobutton.button({
				icons: { secondary: "ui-icon-info" }
			})
			.click(function(e) {
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

			appbutton.button({
			  icons: { primary: "ui-icon-triangle-1-s" }
			})
			.click(function(e) {
			  e.preventDefault();
				if(apps.hasClass('show')) {
					apps.slideUp('fast');
					didHideContainer(apps);
				}
				else {
					apps.slideDown('fast');
					didShowContainer(apps);
				}
			}).click();

            if (apps.hasClass('show')) {
                didShowContainer(apps);
            }
            else {
                apps.hide();
                didHideContainer(apps);
            }

		});
	});
})(this.jQuery);

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

(function (){
    function setupAdGroupForm() {
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
  }

});

(function($) {

    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };


    function setupAdGroupForm() {
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
                            $('form#campaign_and_adgroup #submit').button({
                                label: 'Success...',
                                disabled: true
                            });
                        } else {
                            validator.showErrors(jsonData.errors);
                            $('form#campaign_and_adgroup #submit').button({
                                label: 'Try Again',
                                disabled: false
                            });
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        $('form#campaign_and_adgroup #submit').button({
                            label: 'Try Again',
                            disabled: false
                        });
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
    }


    /*
     * ## initializeDateButtons
     * Loads all click handlers/visual stuff for the date buttons. Used
     * on a ton of pages, probably could be refactored by someone brave
     * enough.
     */
    function initializeDateButtons () {
        $('#dashboard-dateOptions input').click(function() {
            var option = $(this).val();
            if (option == 'custom') {
                $('#dashboard-dateOptions-custom-modal').dialog({
                    width: 570,
                    buttons: [
                        {
                            text: 'Set dates',
                            css: { fontWeight: '600' },
                            click: function() {
                                var from_date = $('#dashboard-dateOptions-custom-from').datepicker("getDate");
                                var to_date = $('#dashboard-dateOptions-custom-to').datepicker("getDate");
                                var num_days = Math.ceil((to_date.getTime()-from_date.getTime())/(86400000)) + 1;

                                var from_day = from_date.getDate();
                                // FYI, months are indexed from 0
                                var from_month = from_date.getMonth() + 1;
                                var from_year = from_date.getFullYear();

                                $(this).dialog("close");
                                var location = document.location.href.replace(/\?.*/,'');
                                document.location.href = location
                                    + '?r=' + num_days
                                    + '&s=' + from_year + "-" + from_month + "-" + from_day;
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
            } else {
                // Tell server about selected option to get new data
                var location = document.location.href.replace(/\?.*/,'');
                document.location.href = location + '?r=' + option;
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
                var date = $.datepicker.parseDate(instance.settings.dateFormat
                                                  || $.datepicker._defaults.dateFormat,
                                                  selectedDate,
                                                  instance.settings);
                other.datepicker('option', 'minDate', date);
            }
        });

        $('#dashboard-dateOptions-custom-to').datepicker({
            defaultDate: '-1d',
            maxDate: '0d',
            onSelect: function(selectedDate) {
                var other = $('#dashboard-dateOptions-custom-from');
                var instance = $(this).data("datepicker");
                var date = $.datepicker.parseDate(instance.settings.dateFormat ||
                                                  $.datepicker._defaults.dateFormat,
                                                  selectedDate,
                                                  instance.settings);
                other.datepicker('option', 'maxDate', date);
            }
        });
    }


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
            var row = $(this);
            if(!row.hasClass('active')) {
                row.siblings().removeClass('active');
                row.addClass('active');
                $('#dashboard-stats-chart').fadeOut(100, function() {
                    mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
                    $(this).show();
                });
            }
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
                var app_key = adunit.get('app_key');
                var app = new App({ id: app_key });
                app.url = function() {
                    return '/api/adgroup/'
                        + adgroup_key
                        + '/apps/'
                        + app_key;
                };

                app.bind('change', function(current_app) {
                    var appView = new AppView({
                        model: app,
                        el: "dashboard-app"
                    });
                    appView.renderInline();
                });

                app.fetch({
                    error: function () {
                        app.fetch({
                            error: toast_error
                        });
                    }
                });

                var adunitView = new AdUnitView({
                    model: adunit,
                    el: "dashboard-app"
                });
                adunitView.renderInline();
            });
        });

        adgroup_inventory.fetch({
            error: function () {
                adgroup_inventory.fetch({
                    error: toast_error
                });
            }
        });
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
            gtee_adgroups.each(function(adgroup) {
                adgroup.fetch({
                    data: ajax_query_string,
                    error: function() {
                        adgroup.fetch({ error: toast_error });
                    }
                });
            });

            // Promotional
            var promo_adgroups = new AdGroups(promo_adgroups_data);
            var promo_adgroups_view = new AdGroupsView({
                collection: promo_adgroups,
                el: '#promo-adgroups',
                title: 'Promotional Campaigns',
                type: 'promo'
            });
            promo_adgroups_view.render();
            promo_adgroups.each(function(adgroup) {
                adgroup.fetch({
                    data: ajax_query_string,
                    error: function() {
                        adgroup.fetch({ error: toast_error });
                    }
                });
            });

            // Backfill Promotional
            var backfill_promo_adgroups = new AdGroups(backfill_promo_adgroups_data);
            var backfill_promo_adgroups_view = new AdGroupsView({
                collection: backfill_promo_adgroups,
                el: '#backfill-promo-adgroups',
                title: 'Backfill Promotional Campaigns',
                type: 'backfill_promo'
            });
            backfill_promo_adgroups_view.render();
            backfill_promo_adgroups.each(function(adgroup) {
                adgroup.fetch({
                    data: ajax_query_string,
                    error: function() {
                        adgroup.fetch({ error: toast_error });
                    }
                });
            });


            // TODO: move somewhere else
            $('#campaigns-appFilterOptions').selectmenu({
                style: 'popup',
                maxHeight: 300,
                width:184
            });

            $("#campaigns-filterOptions, #campaigns-appFilterOptions")
                .change(function() {
                    gtee_adgroups_view.render();
                    promo_adgroups_view.render();
                    backfill_promo_adgroups_view.render();
                });

            // Ad Campaign button
            $("#add_campaign_button").button({
                icons : { primary : 'ui-icon-circle-plus'}
            });

            // AdGroups form
            var actions = ['pause', 'resume', 'activate', 'archive', 'delete'];
            $.each(actions, function(iter, action) {
                $('#campaignForm-' + action).click(function(e) {
                    e.preventDefault();
                    $('#campaignForm')
                        .find("#action")
                        .attr("value", action)
                        .end()
                        .submit();
                });
            });

            $('#campaigns-filterOptions').buttonset({
                disabled: false
            });
        },

        initializeAdGroupDetail: function(bootstrapping_data) {
            var kind = bootstrapping_data.kind,
                adgroup_key = bootstrapping_data.adgroup_key;

            initializeCreativeForm();
            initializeChart();
            initializeDailyCounts();
            initializeDateButtons();
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

            var actions = ['pause', 'resume', 'activate', 'archive', 'delete'];
            $.each(actions, function(iter, action) {
                $('#campaignForm-' + action)
                    .click(function(e) {
                        e.preventDefault();
                        $('#campaignForm')
                            .find("#action")
                            .attr("value", action)
                            .end()
                            .submit();
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

        },
        initializeCreateCampaign: function (bootstrapping_data) {
            setupAdGroupForm();
        }
    };

    window.CampaignsController = CampaignsController;

})(this.jQuery);

(function(e){function b(){e(".appData-details").each(function(){var j=e(this);var k=e(".appData-details-inner",j);var i=e(".appData-details-toggleButton",j);function m(){var n=e(".ui-button-text",i);if(n.length===0){n=i}return n}function h(){k.removeClass("hide");k.addClass("show");i.button("option",{icons:{primary:"ui-icon-triangle-1-n"}});m().text("Hide details")}function l(){k.removeClass("show");k.addClass("hide");i.button("option",{icons:{primary:"ui-icon-triangle-1-s"}});m().text("Show details")}if(k.hasClass("show")){h()}else{k.hide();l()}i.click(function(n){n.preventDefault();if(k.hasClass("show")){k.slideUp("fast");l()}else{k.slideDown("fast");h()}})})}function f(i){e("#creativeManagementForm-action").val(i);var h=e("#creativeManagementForm");h.find('input[name="key"]').remove();e("#advertiser-creativeData").find('input[name="creativeManagementForm-key"]:checked').each(function(j){e(this).val();e("<input></input>").attr("name","key").attr("type","hidden").val(e(this).val()).appendTo(h)});h.submit()}function d(){e('#creativeCreateForm input[name="ad_type"]').click(function(h){e(".adTypeDependent","#creativeCreateForm").hide();e(".adTypeDependent."+e(this).val(),"#creativeCreateForm").show()}).filter(":checked").click();e(".format-options").change(function(h){h.preventDefault();if(e(this).val()=="custom"){e(this).parents("form").find(".customc_only").show()}else{e(this).parents("form").find(".customc_only").hide()}if(e(this).val().search(/full/i)!=-1){e(this).parents().find(".full_only").show()}else{e(this).parents().find(".full_only").hide()}}).change();e("#creativeCreateForm-submit").button({icons:{secondary:"ui-icon-circle-triangle-e"}}).click(function(h){h.preventDefault();e("#creativeCreateForm-loading").show();e("#creativeCreateForm").submit()});e("#creativeCreateForm-cancel").button().click(function(h){h.preventDefault();e("#advertiser-creativeAddForm").slideUp("fast",function(){e("#advertiser-adgroups-addCreativeButton").show()})});e('.creativeEditForm input[name="ad_type"]').click(function(i){var h=e(this).parents("form");e(".adTypeDependent",h).hide();e(".adTypeDependent."+e(this).val(),h).show()}).filter(":checked").click();e(".creativeFormAdvancedToggleButton").button("option",{icons:{primary:"ui-icon-triangle-1-s"}}).click(function(i){i.preventDefault();var h=e(this).parents("form").find(".creativeForm-advanced-options");if(h.is(":hidden")){h.slideDown("fast").removeClass("hidden");e(this).button("option",{icons:{primary:"ui-icon-triangle-1-n"}});e(".ui-button-text",this).text("Less Options")}else{h.slideUp("fast").addClass("hidden");e(this).button("option",{icons:{primary:"ui-icon-triangle-1-s"}});e(".ui-button-text",this).text("More Options")}});e(".creativeAddForm-url-helpLink").click(function(h){h.preventDefault();e("#creativeAddForm-url-helpContent").dialog({buttons:{Close:function(){e(this).dialog("close")}}})});e('#creativeAddForm input[name="creative_type"]').click(function(h){e("#creativeCreate-text_icon").hide();e("#creativeCreate-image").hide();e("#creativeCreate-html").hide();e("#creativeCreate-"+e(this).val()).show()}).filter(":checked").click();e("#creativeAddForm-cancel").button().click(function(h){h.preventDefault();e("#advertiser-creativeAddForm").slideUp("fast",function(){e("#advertiser-adgroups-addCreativeButton").show()})});e("#creativeCreateForm").ajaxForm({data:{ajax:true},dataType:"json",success:function(h){e("#creativeCreateForm-loading").hide();if(h.success){e("#creativeCreateForm-success").show();window.location.reload()}else{e.each(h.errors,function(i,l){e(".form-error-text","#creativeCreateForm").remove();var j=l[0];var k=e("<div>").append(l[1]).addClass("form-error-text");e("input[name="+j+"]","#creativeCreateForm").addClass("error").parent().append(k)});d();window.location.hash="";window.location.hash="advertiser-creativeAddForm";e("#campaignAdgroupForm-submit").button({label:"Continue",disabled:false})}},error:function(h,j,i){}});e(".creativeEditForm").each(function(j){var k=e(this);var h={data:{ajax:true},dataType:"json",success:function(l,m,n,i){i.find(".creativeEditForm-loading").hide();if(l.success){i.find(".creativeCreateForm-success").show();i.parent();i.find(".creativeCreateForm-success").hide();window.location.reload()}else{e(".form-error-text",i).remove();e.each(l.errors,function(o,r){var p=r[0];var q=e("<div>").append(r[1]).addClass("form-error-text");e("input[name="+p+"]",i).addClass("error").parent().append(q)});e('.creativeEditForm input[name="ad_type"]').click(function(o){e(this).parents("form").find(".adTypeDependent").hide().end().find("."+e(this).val()).show().end()}).filter(":checked").click();window.location.hash="";window.location.hash=i.prev("a").attr("name")}}};e(this).ajaxForm(h)});e(".creativeEditForm-submit").button().click(function(h){h.preventDefault();e(this).parents("form").find(".creativeEditForm-loading").show();e(this).parents("form").submit()});e(".creativeEditForm-cancel").button().click(function(h){h.preventDefault();e(this).parents(".advertiser-creativeEditForm").dialog("close")})}function c(){function h(){var i=e("#dashboard-stats .stats-breakdown .active");if(i.attr("id")=="stats-breakdown-ctr"){return"line"}else{return"area"}}e(".stats-breakdown tr").click(function(i){var j=e(this);if(!j.hasClass("active")){j.siblings().removeClass("active");j.addClass("active");e("#dashboard-stats-chart").fadeOut(100,function(){mopub.Chart.setupDashboardStatsChart(h());e(this).show()})}});mopub.Chart.setupDashboardStatsChart(h())}function a(i){var h=new AdUnitCollection();h.adgroup_key=i;h.url=function(){return"/api/adgroup/"+this.adgroup_key+"/adunits/"};h.bind("reset",function(j){j.each(function(l){var k=l.get("app_key");console.log(l);console.log(k);var m=new App({id:k});m.url=function(){return"/api/adgroup/"+i+"/apps/"+k};m.bind("change",function(o){var p=new AppView({model:m,el:"dashboard-app"});p.renderInline()});m.fetch();var n=new AdUnitView({model:l,el:"dashboard-app"});n.renderInline()})});h.fetch()}var g={initializeDirectSold:function(m){var i=m.gtee_adgroups_data,n=m.promo_adgroups_data,j=m.backfill_promo_adgroups_data,q=m.ajax_query_string;var k=new AdGroups(i);var l=new AdGroupsView({collection:k,el:"#gtee-adgroups",tables:{"High Priority":function(s){return s.get("level")=="high"},"Normal Priority":function(s){return s.get("level")=="normal"},"Low Priority":function(s){return s.get("level")=="low"}},title:"Guaranteed Campaigns",type:"gtee"});l.render();k.each(function(s){s.fetch({data:q})});var o=new AdGroups(n);var r=new AdGroupsView({collection:o,el:"#promo-adgroups",title:"Promotional Campaigns",type:"promo"});r.render();o.each(function(s){s.fetch({data:q})});var h=new AdGroups(j);var p=new AdGroupsView({collection:h,el:"#backfill-promo-adgroups",title:"Backfill Promotional Campaigns",type:"backfill_promo"});p.render();h.each(function(s){s.fetch({data:q})});e("#campaigns-appFilterOptions").selectmenu({style:"popup",maxHeight:300,width:184});e("#campaigns-filterOptions, #campaigns-appFilterOptions").change(function(){l.render();r.render();p.render()});e("#add_campaign_button").button({icons:{primary:"ui-icon-circle-plus"}});e.each(["pause","resume","activate","archive","delete"],function(s,t){e("#campaignForm-"+t).click(function(u){u.preventDefault();e("#campaignForm").find("#action").attr("value",t).end().submit()})})},initializeAdGroupDetail:function(j){var i=j.kind,h=j.adgroup_key;d();c();b();a(h);e("#campaign-status-options").change(function(k){var l=e(this).val();e("#fake-campaignForm").find("#action").attr("value",l).end().submit()});e("#campaign-status-options-menu").find("li").first().hide();e.each(["pause","resume","delete"],function(k,l){e("#creativeManagementForm-"+l).click(function(m){m.preventDefault();f(l)})});e(".creativeManagementForm-key").change(function(l){e('#creativeManagementForm input[name="key"]').remove();e(".creativeManagementForm-key:checked").each(function(m){e(this).val()});var k=e("#creativeManagementForm")});e(".advertiser-inLineCreativePreview").button({icons:{primary:"ui-icon-search"}}).click(function(o){o.preventDefault();var l=e(this).attr("id");var n=e("#"+l+"-preview-src").val();var m=parseInt(e("#"+l+"-preview iframe").attr("width"));var k=parseInt(e("#"+l+"-preview iframe").attr("height"));e("#"+l+"-preview iframe").attr("src",n);e("#"+l+"-preview").dialog({buttons:[{text:"Close",click:function(){e(this).dialog("close")}}],width:m+100,height:k+130})});e(".advertiser-inLineCreativeToggle").button({icons:{primary:"ui-icon-wrench"}}).click(function(l){l.preventDefault();var k=e(this).attr("id");var m=e("#"+k+"-edit");m.dialog({width:1000})});e("#add_campaign_button").button({icons:{primary:"ui-icon-circle-plus"}});e("#advertiser-adgroups-addCreativeButton").button({icons:{primary:"ui-icon-circle-plus"}}).click(function(k){k.preventDefault();var l=e("#advertiser-creativeAddForm");if(l.is(":hidden")){e("#advertiser-creativeAddForm").slideDown("fast")}else{e("#advertiser-creativeAddForm").slideUp("fast")}});e("#advertisers-addCampaign").button({icons:{primary:"ui-icon-circle-plus"}});e("#advertisers-adgroups-editAdGroupButton").button({icons:{primary:"ui-icon-wrench"}});e.each(["pause","resume","activate","archive","delete"],function(k,l){e("#campaignForm-"+l).click(function(m){m.preventDefault();e("#campaignForm").find("#action").attr("value",l).end().submit()})});e("#campaign-status-options-menu").find("li").first().hide();e("#advertiser-adgroups-exportSelect").change(function(k){k.preventDefault();var l=e(this).val();if(l!="exp"){e("#campaignExportForm").find("#campaignExportType").val(l).end().submit()}e(this).selectmenu("index",0)});e("#advertiser-adgroups-exportSelect-menu").find("li").first().hide();e("#device_targeting_False").click(function(){e("#target-by-device").slideUp()});e("#device_targeting_True").click(function(){e("#target-by-device").slideDown()});if(e("#device_targeting_True:checked").length===0){e("#target-by-device").hide()}if(e(".creativeData").length===0&&i!="network"){e("#chartWrapper").hide();e("#advertiser-creativeData").hide();e("#advertiser-adgroups-addCreativeButton").click()}}};window.CampaignsController=g})(this.jQuery);
/*
 * # Mopub Marketplace JS
 */
var mopub = mopub || {};

// depends underscore, backbone, jquery, mopub.chart, mopub.util
(function($, _) {

    /*
     * ## Marketplace utility methods
     */

    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    /*
     * Fetches and renders all apps from a list of app_keys.
     * Useful for bootstrapping table loads.
     */
    function fetchAllApps (app_keys) {
        _.each(app_keys, function(app_key) {
            var app = new App({ id: app_key, stats_endpoint: 'mpx' });
            app.bind('change', function(current_app) {
                var appView = new AppView({
                    model: current_app,
                    el: 'marketplace-apps'
                });
                appView.render();
            });

            app.fetch({
                success: function(){
                    $('table').trigger('update');
                },
                error: function () {
                    app.fetch({
                        error: toast_error
                    });
                }
            });
        });
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
                var appView = new AppView({
                    model: current_app,
                    el: 'marketplace-apps'
                });
                appView.renderInline();
            });
            app.fetch({
                error: function () {
                    app.fetch({
                        error: toast_error
                    });
                }
            });
        });
    }

    /*
     * Fetches AdUnit stats over ajax and renders them in already
     * existing table rows.  This method is useful for decreasing page
     * load time. Uses a parent app's key to bootstrap the fetch.
     */
    function fetchAdunitStats (app_key, marketplace_active) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;
        adunits.stats_endpoint = 'mpx';
        // Once the adunits have been fetched from the server,
        // render them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {
            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                adunit.app_id = app_key;
                var adunitView = new AdUnitView({
                    model: adunit,
                    el: '#marketplace_stats'
                });
                adunitView.renderInline();
            });
        });
        adunits.fetch({
            success: function(){
                // Trigger any event handlers that have been attached
                // to the table.  Shouldn't this only trigger for the
                // table that the adunit stats are being placed in?
                $('table').trigger('update');
                $("#" + app_key + "-img").hide();
                if (!marketplace_active) {
                    $(".targeting-box").attr('disabled', true);
                }
            },
            error: function () {
                adunits.fetch({
                    error: toast_error
                });
            }
        });
    }

    /*
     * Fetches and renders all of the adunits from an app key.  Useful
     * for showing adunits when a user has clicked on a 'show adunits'
     * link.
     */
    function fetchAdunitsForApp (app_key) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;

        // Once the adunits have been fetched from the server, render
        // them as well as the app's price floor range
        adunits.bind('reset', function(adunits_collection) {

            // Get the max and min price floors from the adunits so we
            // can use them for the app's price floor range
            var high = _.max(adunits_collection.models, function(adunit){
                 return adunit.get("price_floor");
            }).get("price_floor");

            var low = _.min(adunits_collection.models, function(adunit){
                return adunit.get("price_floor");
            }).get("price_floor");

            // Set the app's price floor cell to the range of the
            // adunits Keep the "Edit Price Floor" button
            var btn = $("<a href='#" + app_key +"'" +
                        " class='edit_price_floor' " +
                        "id='" + app_key + "'> "
                        + "Edit Price Floor</a>");

            // Display the range of price floors for the app. (This is
            // no longer used, but left in because it could be used
            // again in the future).
            if (high == low) {
                $(".app-row#app-" + app_key + " .price_floor").html("All $" + high);
            } else {
                $(".app-row#app-" + app_key + " .price_floor").html("$" + low + " - " + "$" + high);
            }

            // Disable the 'view' link in the app row under the targeting column
            $(".app-row#app-" + app_key + " .view_targeting").addClass("hidden");

            // Create the views and render each adunit row
            _.each(adunits_collection.models, function(adunit) {
                var adunitView = new AdUnitView({
                    model: adunit,
                    el: 'marketplace-apps'
                });
                adunitView.render();
            });
        });

         adunits.fetch({
             error: function() {
                 adunits.fetch({
                     error: toast_error
                 });
             }
         });
    }

    /*
     * If an adunit row has for-app-[app_id] as a class,
     * strip the app_id and return it. Used for sorting
     * adunit rows underneath their apps.
     */
    function getAppId (adunit) {

        adunit = $(adunit);
        var app_id = '';
        var adunit_classes = adunit.attr('class').split(' ');

        _.each(adunit_classes, function(adunit_class) {
            if (adunit_class.search('for-app-') >= 0) {
                app_id = adunit_class.replace('for-app-', '');
            }
        });

        return app_id;
    }

    /*
     * Sends the AJAX request to turn ON the marketplace.
     * This shouldn't just return true, it should return true
     * only when no errors are returned from the server. Fix this.
     */
    function turnOn () {
        var on = $.post('/campaigns/marketplace/activation/', {
            activate: 'true'
        });

        on.error(function() {
            Toast.error("There was an error saving your Marketplace settings. Our support team has been notified. Please refresh your page and try again.");
        });

        on.done(function() { });

        $(".targeting-box").removeAttr('disabled');
        $("#blindness").removeAttr('disabled');
        return true;
    }

    /*
     * Sends the AJAX request to turn OFF the marketplace.
     * This shouldn't just return true, it should return true
     * only when no errors are returned from the server. Fix this.
     */
    function turnOff () {
        var off = $.post('/campaigns/marketplace/activation/', {
            activate: 'false'
        });
        $(".targeting-box").attr('disabled', true);
        $("#blindness").attr('disabled', true);
        return true;
    }

    /*
     * Makes the Creatives Performance tab's datatable
     */
    function makeCreativePerformanceTable (pub_id, blocklist, start_date, end_date) {

        var origin;
        if (!window.location.origin) {
            origin = window.location.protocol
                + "//" + window.location.host + "/";
            window.location.origin = origin;
        } else {
            origin = window.location.origin;
        }

        var creative_data_url = origin
            + "/campaigns/marketplace/creatives/";
        var table = $("#report-table").dataTable({
            bProcessing: true,
            // Use jQueryUI to style the table
            bJQueryUI: true,
            // Add page numbers to the table instead of just prev/next buttons
            sPaginationType: "full_numbers",
            // Message that appears when the table is empty
            oLanguage: {
                sEmptyTable: "No creatives have been displayed for this time range."
            },
            // Column Width
            aoColumns:[
                {sWidth: "330px"}, // Creative iFrame
                {sWidth: "190px"}, // Advertiser
                {sWidth: "120px"}, // Revenue
                {sWidth: "90px"},  // eCPM
                {sWidth: "90px"}   // Impressions
                //{"sWidth": "80px"}, // Clicks
                //{"sWidth": "80px"}, // CTR
            ],
            // Don't resize table columns automatically, we'll do it manually
            bAutoWidth:false,
            // Sort by revenue descending on table load
            aaSorting: [[2,'desc']],
            // Endpoint to fetch table data
            sAjaxSource: creative_data_url,
            // Tell datatables how to fetch and parse server data
            fnServerData: function( sUrl, aoData, fnCallback ) {
                $.ajax({
                    url: sUrl,
                    data: {
                        pub_id: pub_id,
                        start: start_date,
                        end: end_date,
                        format:'jsonp'
                    },
                    // When the data returns from the endpoint, we have to format it the way
                    // datatables wants. We also have to make sure to get the types of each
                    // data the way we want them if we want sorting to work correctly.
                    success: function(data, textStatus, jqXHR) {

                        var creative_data = _.map(data, function(creative, key) {
                            var ecpm = (creative['stats']['pub_rev'] / (creative['stats']['imp']+1))*1000;
                            return [
                                creative["creative"]["url"],
                                creative["creative"]["ad_dmn"],
                                creative["stats"]["pub_rev"].toFixed(2),
                                creative["stats"]["imp"],
                                ecpm
                            ];
                        });

                        var response = {
                            aaData: creative_data
                        };
                        fnCallback(response, textStatus, jqXHR);
                    },
                    dataType: "jsonp",
                    cache: false
                } );
            },
            // Callback function that takes table data and renders it
            // as a table row. Called on each row's data right before
            // it's rendered in the table (i.e. when a user clicks
            // 'next'/'prev', or changes the number of displayed rows)
            fnRowCallback: function(nRow, aData, iDisplayIndex) {

                $("td:eq(0)", nRow).html("<iframe width='320px' height='50px' src='" +
                                         aData[0] +
                                         "'></iframe>");

                var domain = aData[1];
                if (_.contains(blocklist, domain)) {
                    $("td:eq(1)", nRow).text(domain + " (Blocked)");
                } else if (domain != null) {
                    // Please leave this commented. This feature will be uncommented and used
                    // in the future. Thanks.
                    // var anchor = $("<a href='#'> Block </a>").click(function (event) {
                    //     var $this = $(this);
                    //     event.preventDefault();
                    //     var blocklist_xhr = $.post("/campaigns/marketplace/settings/blocklist/", {
                    //         action: 'add',
                    //         blocklist: domain
                    //     });
                    //     blocklist_xhr.done(function() {
                    //         $this.parent().append(' (Blocked)');
                    //         $this.remove();
                    //     });
                    // });
                    $("td:eq(1)", nRow).html(domain);
                } else {
                    $("td:eq(1)", nRow).html("<span class='muted'>(Unknown)</span>");
                }
                $("td:eq(2)", nRow).addClass("numeric").text("$" + mopub.Utils.formatNumberWithCommas(aData[2]));
                $("td:eq(3)", nRow).addClass("numeric").text(mopub.Utils.formatNumberWithCommas(aData[3]));
                $("td:eq(4)", nRow).addClass("numeric").text(mopub.Utils.formatCurrency(aData[4]));
                return nRow;
            }
        });

        return table;
    }

    /*
     * Adds a domain to the in=page blocklist, along with an
     * anchor + click event to remove it over Ajax.
     */
    function addToBlocklist (domain) {
        var anchor = $("<a href='#'>Remove</a>").click(blocklistRemoveClickHandler);
        var list_item = $("<li></li>").html(domain + " ");
        list_item.append(anchor);
        $("#blocked_domains").append(list_item);
    }

    function blocklistRemoveClickHandler (event) {
        event.preventDefault();

        var anchor = $(this);
        var domain = anchor.attr('id');
        $("img", anchor.parent()).removeClass('hidden');
        var blocklist_xhr = $.post("/campaigns/marketplace/settings/blocklist/", {
            action: 'remove',
            blocklist: domain
        });

        blocklist_xhr.done(function (response) {
            $("img#" + domain).addClass('hidden');
            anchor.parent().fadeOut();
        });

        blocklist_xhr.error(function (response) {
            $("img#" + domain).addClass('hidden');
            Toast.error("There was an error adding to your blocklist. Please try again.");
        });
    }

    var MarketplaceController = {
        initializeIndex: function (bootstrapping_data) {

            // Fill in the stats data for each of the apps and
            // each of their adunits
            fetchAppStats(bootstrapping_data.app_keys);
            _.each(bootstrapping_data.app_keys, function(app_key) {
                fetchAdunitStats(app_key, bootstrapping_data.marketplace_active);
            });

            var table = makeCreativePerformanceTable(bootstrapping_data.pub_key,
                                                     bootstrapping_data.blocklist,
                                                     bootstrapping_data.start_date,
                                                     bootstrapping_data.end_date);

            /*
             * Click handling for the stats breakdown
             * REFACTOR: move this to a common place because it's everywhere
             */
            $('.stats-breakdown tr').click(function(e) {
                var row = $(this);
                if (!row.hasClass('active')) {
                    var table = row.parents('table');
                    $('tr.active', table).removeClass('active');
                    row.addClass('active');
                }
            });

            /*
             * Blindness settings
             */
            $("#blindness").click(function () {
                var loading_img = $("#blindness-spinner").show();
                var saving = $("#blindness-save-status .saving").show();

                var blindness_xhr = $.post("/campaigns/marketplace/settings/blindness/",{
                    activate: $(this).is(":checked")
                });

                blindness_xhr.done(function(data){
                    loading_img.hide();
                    saving.hide();
                    if (data.hasOwnProperty('success')) {
                        var saved = $("#blindness-save-status .saved").show();
                        setTimeout(function() { saved.fadeOut(); }, 1000);
                    } else {
                        var errored = $("#blindness-save-status .error").show();
                        setTimeout(function() {errored.fadeOut(); }, 1000);
                    }
                });
            });

            /*
             * Table sorting doesn't work the way we'd like when adunits have been
             * displayed. We'd like them to sort underneath their apps. Without
             * this formatter function, they sort independently.
             */
            $.tablesorter.addWidget({
                id: 'adunitSorting',
                format: function(table) {
                    var app_id_cache = {};

                    $('.adunit-row', table).each(function(iter, item) {
                        // find the app row for the adunit
                        var app_id = Marketplace.getAppId(item);
                        var app;
                        if (app_id_cache.hasOwnProperty(app_id)) {
                            app = app_id_cache(app_id);
                        } else {
                            app = $('.app-row#app-' + app_id);
                        }
                        // remove the adunit from it's current location
                        $(item).remove();
                        // and place it after the app row
                        app.after(item);
                    });
                }
            });

            /*
             * Set up the marketplace table. By default we're going to sort by app name.
             * Icons (header 0), price floors (header 6) and targeting (header 7) columns
             * can't be sorted because that just doesn't make sense fool.
             */
            // $('marketplace-apps').tablesorter({
            //     widgets: ['adunitSorting'],
            //     sortList: [[1, 0]],
            //     headers: { 0: { sorter: false}, 6: {sorter: false}, 7: {sorter: false} }
            // });

            /*
             * Functionality for blocking advertisers from the creatives performance table
             */
            $('a.block').click(function (event) {
                event.preventDefault();
                var block_link = $(this);
                var domain = $(this).attr('id');
                $.ajax({
                    type: 'post',
                    url: '/campaigns/marketplace/settings/blocklist/',
                    data: {
                        blocklist: domain,
                        action: "add"
                    },
                    success: function (a,b) {
                        block_link.text("Blocked").unbind("click").click(function(){
                            return false;
                        });
                    }
                });
            });

            /*
             * Make the lightswitches turn the Marketplace on and off.
             * They're all bound to the same selector so that any time someone
             * clicks the Marketplace On/Off switch, all of them get turned off.
             */
            $(".lightswitch").lightswitch(turnOn, turnOff);

            /*
             * Toasts for the top and bottom lightswitches. Toasts are little flash messages
             * that let the user know something has happened. These should be rolled up
             * into their own library and put in mopub.js. For now they're here because
             * this is the only place they're used.
             *
             * # REFACTOR: use the new kind of toast
             */
            $("#top_switch").click(function() {
                if ( $("#top_switch .switch").hasClass('on') ) {
                    $("#first_time_toast").fadeIn();
                    setTimeout(function() {
                        $("#first_time_toast").fadeOut();
                    }, 3000);
                }
            });

            $("#bottom_switch").click(function() {
                if ( $("#bottom_switch .switch").hasClass('off') ) {
                    $("#settings_toast").fadeIn();
                    setTimeout(function() {
                        $("#settings_toast").fadeOut();
                    }, 3000);
                }
            });

            /*
             * ## Blocklist adding/editing
             * Click/form handlers and ajax stuff for the blocklist
             * in the settings tab
             */
            $('#blocklist-submit').click(function(e) {
                e.preventDefault();
                var blocklist = $("textarea[name='blocklist']").val();
                var blocklist_xhr = $.post('/campaigns/marketplace/settings/blocklist/', {
                    action: 'add',
                    blocklist: blocklist
                });

                blocklist_xhr.done(function (response) {
                    var domains = response['new'];
                    $.each(domains, function(iter, domain) {
                        addToBlocklist(domain);
                    });
                    $("textarea[name='blocklist']").val('');
                });

                blocklist_xhr.error(function (response) {
                    Toast.warning(response);
                });
            });

            /*
             * ## Blocklist removal
             */
            $("a.blocklist_remove").click(blocklistRemoveClickHandler);

            /*
             * ## Content filtering
             */

            $("input.content_level").click(function(){
                var self = $(this);
                var filter_level = self.attr('value');
                var loading_img = $("#filter-spinner").show();
                var saving = $("#filter-save-status .saving").show();
                var result = $.post("/campaigns/marketplace/settings/content_filter/", {
                    filter_level: filter_level
                });

                result.success(function(data){
                    loading_img.hide();
                    saving.hide();
                    if (data.hasOwnProperty('success')) {
                        var saved = $("#filter-save-status .saved").show();
                        setTimeout(function() { saved.fadeOut(); }, 1000);

                    } else {
                        var errored = $("#filter-save-status .error").show();
                        setTimeout(function() {errored.fadeOut(); }, 1000);
                    }
                });
            });




            /*
             * F THIS.
             * REFACTOR.
             *
             * Everything here and below needs to not exist in this file, because
             * it already exists in two other files. Obvo refactor.
             */
            function getCurrentChartSeriesType() {
                var activeBreakdownsElem = $('#dashboard-stats .stats-breakdown .active');
                if (activeBreakdownsElem.attr('id') == 'stats-breakdown-ecpm') return 'line';
                else return 'area';
            }

            $('.stats-breakdown tr').click(function(e) {
                $('#dashboard-stats-chart').fadeOut(100, function() {
                    mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
                    $(this).show();
                });
            });

            var dailyStats = mopub.accountStats["daily"];
            mopub.dashboardStatsChartData = {
                pointStart: mopub.graphStartDate,
                pointInterval: 86400000,
                revenue: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "revenue")}],
                impressions: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "impressions")}],
                ecpm: [{ "Total": mopub.Stats.statArrayFromDailyStats(dailyStats, "ecpm")}]
            };
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());

            // set up dateOptions
            $('#dashboard-dateOptions input').click(function() {
                var option = $(this).val();
                var hash = document.location.hash;
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
                                    var location = document.location.href.replace(hash, '').replace(/\?.*/,'');
                                    document.location.href = location +
                                        '?r=' + num_days +
                                        '&s=' + from_year + "-" + from_month + "-" + from_day +
                                        hash;
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
                } else {
                    // Tell server about selected option to get new data
                    var location = document.location.href.replace(hash,'').replace(/\?.*/,'');
                    document.location.href = location+'?r=' + option + hash;
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
                    var date = $.datepicker
                        .parseDate(instance.settings.dateFormat ||
                                   $.datepicker._defaults.dateFormat,
                                   selectedDate,
                                   instance.settings);
                    other.datepicker('option', 'minDate', date);
                }
            });
            $('#dashboard-dateOptions-custom-to').datepicker({
                defaultDate: '-1d',
                maxDate: '0d',
                onSelect: function(selectedDate) {
                    var other = $('#dashboard-dateOptions-custom-from');
                    var instance = $(this).data("datepicker");
                    var date = $.datepicker
                        .parseDate(instance.settings.dateFormat ||
                                   $.datepicker._defaults.dateFormat,
                                   selectedDate,
                                   instance.settings);
                    other.datepicker('option', 'maxDate', date);
                }
            });

        }
    };

    window.MarketplaceController = MarketplaceController;

})(this.jQuery, this._);

/*
 * # MoPub Global JS
 */

//For JSLint Validation:
//global console: true, Highcharts: true

//mopub singleton object
var mopub = mopub || {};
mopub.Utils = mopub.Utils || {};

/*
 * Make sure there's a console.log function in case we forgot to remove debug statements
 */
if (typeof window.console == "undefined") {
    window.console = {
        log: function() {}
    };
}

/*
 * # Global document.ready function
 * If you want something to happen everywhere, on every page,
 * it should go here.
 */
(function($) {

    var mopub = window.mopub || {};
    var Chart = window.Chart || {};
    var Stats = window.Stats || {};

    $(document).ready(function() {

        /*
         * ## Mixpanel Event Tracking
         */

        if (typeof mpq.push != 'undefined') {
            // Date options in dashboard
            try {
                $("#dashboard-dateOptions-option-7").click(function(){
                    mpq.push(['track', '7 Day Date-option clicked']);
                });
                $("#dashboard-dateOptions-option-14").click(function(){
                    mpq.push(['track', '14 Day Date-option clicked']);
                });
                $("#dashboard-dateOptions-option-30").click(function(){
                    mpq.push(['track', '30 Day Date-option clicked']);
                });
                $("#dashboard-dateOptions-option-custom").click(function(){
                    mpq.push(['track', 'Custom Date-option clicked']);
                });
                // Today/Yesterday/All options in rollup
                $("#stats-breakdown-dateOptions-option-0").click(function(){
                    mpq.push(['track', '"Today" clicked in Stats Breakdown']);
                });
                $("#stats-breakdown-dateOptions-option-1").click(function(){
                    mpq.push(['track', '"Yesterday" clicked in Stats Breakdown']);
                });
                $("#stats-breakdown-dateOptions-option-2").click(function(){
                    mpq.push(['track', '"All" clicked in Stats Breakdown']);
                });
            } catch (x) {

            }
        }

        // marketplace hiding
        if ($('#is_admin_input').val()=='False') {
            $('.marketplace').hide();
        }

        // preload images (defined below)
        var JQUERY_UI_IMAGE_PATH = '/js/libs/jquery-ui-1.8.7.custom/css/mopub/images';
        $.preLoadImages(
            '/images/ui/ui-button-active.png',
            '/images/ui/ui-button-default.png',
            '/images/ui/ui-button-hover.png',
            '/images/ui/ui-icons-active.png',
            '/images/ui/ui-icons-focus.png',
            '/images/ui/ui-icons-hover.png',
            '/images/ui/ui-icons-progress.png',
            JQUERY_UI_IMAGE_PATH + '/ui-bg_highlight-hard_25_e57300_1x100.png',
            JQUERY_UI_IMAGE_PATH + '/ui-bg_highlight-hard_50_dddddd_1x100.png',
            JQUERY_UI_IMAGE_PATH + '/ui-bg_highlight-hard_100_f3f3f3_1x100.png',
            JQUERY_UI_IMAGE_PATH + '/ui-bg_inset-soft_25_595959_1x100.png',
            JQUERY_UI_IMAGE_PATH + '/ui-icons_0090d9_256x240.png',
            JQUERY_UI_IMAGE_PATH + '/ui-icons_cc2929_256x240.png',
            JQUERY_UI_IMAGE_PATH + '/ui-icons_ffffff_256x240.png',
            '/placeholders/image.gif'
        );

        // replace <legend> with <h2>
        $('legend').each(function() {
            var legend = $(this);
            var h2 = $('<h2>'+legend.html()+'</h2>');
            h2.attr('class', legend.attr('class'));
            h2.attr('id', legend.attr('id'));
            legend.replaceWith(h2);
        });

        // set up buttons
        $('.button').button().css({ visibility: 'visible' });

        // set up buttonsets
        $('.buttonset').buttonset().css({ visibility: 'visible' });

        // gray out any buttonsets that ought to be disabled
        $('.buttonset-start-disabled').buttonset();
        $('.buttonset-start-disabled').buttonset({ disabled: true });

        // set up selectmenus
        $('.selectmenu').selectmenu().css({ visibility: 'visible' });

        // set up validation to be run on form submit
        $('.validate').validate();

        // Tables with the 'sortable' class will be made sortable by default
        $(".sortable").tablesorter();

        // Tabify tabs
        $('.tabs').tabs();
        $('.pills').tabs();

        // Where is this used?
        // $(".tree").treeview();

        // Override default jQuery UI dialog options
        $.extend($.ui.dialog.prototype.options, {
            modal: true,
            resizable: false,
            draggable: false,
            width: 400
        });

        // Override default jQuery UI datepicker options
        $.datepicker.setDefaults({
            dayNamesMin: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        });

        // Set up form placeholders
        $('input[placeholder], textarea[placeholder]').placeholder({ preventRefreshIssues: true });

        // Set up text overflow elements
        $('#titlebar .breadcrumb h1, .dataTable-name .inner').textOverflow(' &hellip;');

        // Set up dropdowns
        $(".dropdown-head").dropdown('.dropdown');

        // Set up alert-message closing
        $(".alert-message .close").click(function() {
            $(this).parent().fadeOut();
        });

        // Set up tooltips.
        // FYI: These are being phased out
        $.fn.qtip.styles.mopub = {
            background: '#303030',
            color: '#ffffff',
            border: {
                radius: 5
            },
            tip: {
                size: {
                    x: 10,
                    y: 10
                }
            },
            name: 'dark' // Inherit the rest of the attributes from the preset dark style
        };

        $('a[title]').qtip({ style: { name: 'mopub', tip: true } });
        $('.formFields-field-help-link[title]').click(function(e) { e.preventDefault(); });



        // Message Center
        // hide message center when page loads if there are no messages
        function hideMessageCenterIfNoMessages() {
            if($('.messageCenter-message').length === 0) {
                $('#messageCenter').hide();
            }
        }
        hideMessageCenterIfNoMessages();

        // Set up "More info" links
        $('.messageCenter-message-moreInfoLink').click(function(e) {
            e.preventDefault();
            var link = $(this);
            var info = $('.messageCenter-message-moreInfo', link.parents('.messageCenter-message'));
            // clone info (so the original doesn't get moved around) and make the dialog
            info.clone().dialog({
                buttons: { "Close": function() { $(this).dialog("close"); } },
                close: function(e, u) { $(this).remove(); } // remove clone
            });
        });

        // Set up "Hide this" links
        $('.messageCenter-message-hide').click(function(e) {
            e.preventDefault();
            var link = $(this);
            var message = link.parents('.messageCenter-message');
            message.fadeOut('fast', function() {
                message.remove();
                hideMessageCenterIfNoMessages();
            });
        });
        // TODO: tell server that message.attr('id') has been hidden

        // Set up stats breakdown
        // Should be done in backbone view
        /*
        $('.stats-breakdown tr').click(function(e) {
            var row = $(this);
            if (!row.hasClass('active')) {
                var table = row.parents('table');
                $('tr.active', table).removeClass('active');
                row.addClass('active');
            }
        });
        */

        // Set up highcharts default options
        Highcharts.setOptions({
            chart: {
                animation: false,
                backgroundColor: null,
                borderRadius: 0,
                margin: [30,0,30,45],
                height: 185
            },
            title: { text: null },
            lang: {
                loading: "Loading ..."
            },
            credits: { enabled: false },
            style: {
                fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif'
            },
            plotOptions: {
                series: {
                    animation: false,
                    shadow: false,
                    stickyTracking: false
                },
                area: {
                    lineWidth: 4,
                    fillOpacity: 0.1,
                    stacking: 'normal',
                    marker: {
                        lineWidth: 2,
                        radius: 5,
                        symbol: 'circle',
                        states: {
                            hover: {
                                lineWidth: 2,
                                radius: 7
                            }
                        }
                    },
                    states: {
                        hover: {
                            lineWidth: 4
                        }
                    }
                }
            },
            xAxis: {
                endOnTick: false,
                gridLineWidth: 0.5,
                gridLineColor: '#dddddd',
                lineWidth: 1,
                lineColor: '#cccccc',
                type: 'datetime',
                labels: {
                    style: {
                        fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                        color: '#999',
                        fontSize: '10px'
                    },
                    y: 20
                },
                dateTimeLabelFormats: {
                    second: '%b %e %l:%M:%S%p',
                    minute: '%b %e %l:%M%p',
                    hour: '%b %e %l:%M%p',
                    day: '%b %e',
                    week: '%b %e',
                    month: '%b %Y',
                    year: '%Y'
                },
                tickColor: '#dddddd',
                tickLength: 5,
                tickWidth: 0.5
            },
            yAxis: {
                showFirstLabel: false,
                showLastLabel: true,
                gridLineWidth: 0.5,
                gridLineColor: '#dddddd',
                min: 0,
                title: {
                    text: null
                },
                labels: {
                    style: {
                        fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                        color: '#999',
                        fontSize: '10px'
                    },
                    x: -5
                }
            },
            legend: {
                borderColor: null,
                borderRadius: 0,
                borderWidth: 0,
                align: 'center',
                verticalAlign: 'top',
                y: -17,
                itemStyle: {
                    fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                    size: '12px',
                    cursor: 'pointer',
                    color: '#444444'
                },
                itemHoverStyle: {
                    color: '#e57300'
                },
                itemHiddenStyle: {
                    color: '#ccc'
                },
                lineHeight: 12,
                symbolPadding: 6,
                symbolWidth: 12
            },
            tooltip: {
                backgroundColor: "rgba(255, 255, 255, .9)",
                style: {
                    fontFamily: '"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',
                    fontSize: '13px',
                    padding: '10px'
                }
            }
        });

        // Set up 'What's This?' dialogs
        $('.whatsthis').live('click', function(e) {
            e.preventDefault();
            $('#'+$(this).attr('id').replace('helpLink', 'helpContent')).dialog({
                buttons: { "Close": function() { $(this).dialog('close');} }
            });
        });


    }); // end $(document).ready

    function getUrlParameters()
    {
        var parameters = {};
        var url_params = window.location.search.slice(1).split('&');
        var param;
        for(var i = 0; i < url_params.length; i++)
        {
            param = url_params[i].split('=');
            parameters[param[0]] = param[1];
        }
        return parameters;
    }

    var url_parameters = getUrlParameters();



    /*
     * # MoPub-defined jQuery utility functions and extensions
     */

    /*
     * ## Image Preloader
     * Caches images for faster loading
     */
    var cache = [];
    $.preLoadImages = function() {
        var args_len = arguments.length;
        for (var i = args_len; i--;) {
            var cacheImage = document.createElement('img');
            cacheImage.src = arguments[i];
            cache.push(cacheImage);
        }
    };

    /*
     * ## Dropdown Menus
         *
             * Usage:
             *
             * `$(dropdown-trigger).dropdown(things-that-dropdown);`
             */
    $.fn.dropdown = function(selector) {
        var self = this;
        var over_trigger, over_body = false;

        // Make sure the dropdown starts closed (in case class="invisible" wasnt set)
        dropdownClose();

        function dropdownOpen() {
            if ($(selector).hasClass('invisible')); {
                $(selector).removeClass('invisible');
            }
            $(self).addClass('hovered');
        }

        function dropdownClose() {
            if (!$(selector).hasClass('invisible')) {
                $(selector).addClass('invisible');
            }
            $(self).removeClass('hovered');
        }

            // Set the hover states
        $(this).hover(function() {
            over_trigger = true;
        }, function () {
            over_trigger = false;
        });

        $(selector).hover(function() {
            over_body = true;
        }, function () {
            over_body = false;
        });

        // Open/close the dropdown if the state has changed
        // Breaks in firefox if setInterval isn't given a number for the time.
        setInterval(function() {
            if (over_trigger || over_body) {
                dropdownOpen();
            } else {
                dropdownClose();
            }
        }, 1);
    };


    /*
     * ## Activity utility functions
     */
    function isActive(item) {
        return item.hasClass('active');
    }

    function activate (element, container) {
        if (container.length > 1) {
            container.each(function(){
                $(this).removeClass('active');
            });
        } else {
            container.find('.active').removeClass('active');
        }
        element.addClass('active');
    }


    /*
     * ## Tabs
     * Turns a ul into horizontal tabs, that can be used to hide and show
     * sections of a page.
     *
     * Usage:
     * `<ul class="tabs">`
     *
     * ` <li class="active"> <a href="#s1">Section 1 </a> </li>`
     *
     * ` <li> <a href="#s2">Section 2 </a> </li>`
     *
     * `</ul>`
     *
     * `<div class="active tab-section" id="s1"></div>`
     *
     * `<div class="tab-section" id="s2"></div>`
     *
     * `$(".tabs").tabs();`
     *
     * TODO: Refactor so that the first tab/section are activated if nothing is activated by default
     */
    $.fn.tabs = function() {
        // find the sections within the page we've marked as tab activate-able
        var tab_sections = $(".tab-section");
        // bind the ul
        var ul = $(this);
        // get the <li>'s within the ul
        var list_items = $('li', ul);
        // add actions to each of the li/a clicks
        $.each(list_items, function(iter, item) {
            // prevent jumping around when a tab is clicked
            var anchor = $('a', item);
            $(anchor).click(function(event){
                event.preventDefault();
            });
            // activate the tab and its section on a click
            var href = anchor.attr('href');
            $(item).click(function(){
                activate($(this), ul);
                activate($(href), tab_sections);
                window.location.hash = href + "-tab";
            });

            if (window.location.hash == href + "-tab") {
                $(item).click();
            }
        });
    };


    /*
     * Escaping/unescaping HTML.
     *
     * Be careful: if you escape html thats already escaped, things get weird.
     */
    $.unescapeHTML = function (html) {
        return $("<div />").html(html).text();
    };

    $.escapeHTML = function (html) {
        return $("<div />").text(html).html();
    };


    /*
     * ## jQuery Lightswitch
     *
     * lightswitch takes two functions, an on function and an off function.
     * When the lightswitch in the page is clicked on or off, the the corresponding
     * function is called. If the function returns true, the switch is slid.
     *
     * Usage:
     *
     * `var on = function() {`
     *
     * `   console.log('BOOMSLAM');`
     *
     * `   return true;`
     *
     * `};`
     *
     *
     * `var off = function() {`
     *
     * `   console.log('SEE YA');`
     *
     * `   return true;`
     *
     * `};`
     *
     * `$(".lightswitch").lightswitch(on, off);`
     *
     * HTML:
     * <div class="lightswitch">
     *   <div class="switch on"></div>
     * </div>
     */
    $.fn.lightswitch = function (on_function, off_function) {

        if (typeof on_function == 'undefined') {
            on_function = function () {
                return true;
            };
        }

        if (typeof off_function == 'undefined') {
            off_function = function () {
                return true;
            };
        }

        var light_switch = $(this);
        var switcher = $('.switch', light_switch);

        light_switch.click(function () {
            if (switcher.hasClass('on')) {
                var result = off_function();
                if (result) {
                    switcher.removeClass('on').addClass('off');
                }

            } else if (switcher.hasClass('off')) {
                var result = on_function();
                if (result) {
                    switcher.removeClass('off').addClass('on');
                }
            } else {
                switcher.addClass('off');
            }
        });
    };

    $.fn.lightswitchOn = function () {
        var light_switch = $(this);
        var switcher = $('.switch', light_switch);
        switcher.removeClass('off').addClass('on');
    };

    $.fn.lightswitchOff = function () {
        var light_switch = $(this);
        var switcher = $('.switch', light_switch);
        switcher.removeClass('on').addClass('off');
    };

    mopub.Utils = mopub.Utils || {};

    /*
     * ## Mopub Utility
     */
    mopub.Utils.formatNumberWithCommas = function(string) {
        string += '';
        var x = string.split('.');
        var x1 = x[0];
        var x2 = x.length > 1 ? '.' + x[1] : '';
        var rgx = /(\d+)(\d{3})/;
        while (rgx.test(x1)) {
            var x1 = x1.replace(rgx, '$1' + ',' + '$2');
        }
        return x1 + x2;
    };

    mopub.Utils.formatCurrency = function(num) {
        return "$" + mopub.Utils.formatNumberWithCommas(num.toFixed(2));
    };

    mopub.Utils.formatNumberAsPercentage = function(string) {
        // We round to two decimal places.
        return (string*100).toFixed(2) + '%';
    };

    mopub.Utils.getKeysFromObject = function(object) {
        var keys = [];
        for (var key in object) {
            if (object.hasOwnProperty(key)) keys.push(key);
        }
        return keys;
    };

    /*
     * ## Stat sorting
     */
    Stats.sortStatsObjectsByStat = function(objects, statName) {
        objects.sort(function(a, b) {
            var statA = parseFloat(a["stats"]["sum"][statName]);
                var statB = parseFloat(b["stats"]["sum"][statName]);
            if (statA < statB) return 1;
            if (statA > statB) return -1;
            else return 0;
        });
        return objects;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.statArrayFromDailyStats = function(arrayOfDailyStats, statName) {
        return $.map(arrayOfDailyStats, function(oneDayStats) {
            return parseFloat(oneDayStats[statName]);
        });
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.getGraphSummedStatsForStatName = function(statName, objects) {
        var result = [];

        var topThreePerformers = objects.splice(0, 3);
        var otherPerformers = objects;

        // Get stats for the top three performers.
        $.each(topThreePerformers, function(index, statsObject) {
                var name = statsObject["key"];
            var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
            var graphStatsObject = {};
            graphStatsObject[name] = Stats.statArrayFromDailyStats(arrayOfDailyStats, statName);
            result.push(graphStatsObject);
        });

        if (otherPerformers.length == 0) return result;

        // Get stats for all other performers.
        var statsForOtherPerformers = Stats.sumDailyStatsAcrossStatsObjects(otherPerformers, statName);
        var otherDict = { "Others": statsForOtherPerformers };
        result.push(otherDict);

        return result;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.sumDailyStatsAcrossStatsObjects = function(objects, statName) {
        var result = [];
        $.each(objects, function(index, statsObject) {
            var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
            $.each(arrayOfDailyStats, function(dayIndex, oneDayStats) {
                if (!result[dayIndex]) result[dayIndex] = 0;
                result[dayIndex] += parseFloat(oneDayStats[statName]);
            });
        });
        return result;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.getGraphCtrStats = function(objects) {
        var result = [];

        var topThreePerformers = objects.splice(0, 3);
        var otherPerformers = objects;

        // Get stats for the top campaigns.
        $.each(topThreePerformers, function(index, statsObject) {
            var name = statsObject["key"];
            var arrayOfDailyStats = statsObject["stats"]["daily_stats"];
            var graphStatsObject = {};
            graphStatsObject[name] = Stats.statArrayFromDailyStats(arrayOfDailyStats, "ctr");
            result.push(graphStatsObject);
        });

        if (otherPerformers.length == 0) return result;

        // Get stats for all other campaigns.
        var statsForOtherPerformers = Stats.getDailyCtrAcrossStatsObjects(otherPerformers);
        var otherDict = { "Others": statsForOtherPerformers };
        result.push(otherDict);

        return result;
    };

    /*
     * ## DOCUMENT THIS
     */
    Stats.getDailyCtrAcrossStatsObjects = function(objects) {
        var ctr = [];
        var clicks = Stats.sumDailyStatsAcrossStatsObjects(objects, "click_count");
        var impressions = Stats.sumDailyStatsAcrossStatsObjects(objects, "impression_count");

        for (var i = 0, len = clicks.length; i < len; i++) {
            ctr[i] = (impressions[i] === 0) ? 0 : clicks[i] / impressions[i];
        }
        return ctr;
    };

    /*
     * ## Dashboard Stats Chart
     */

    /*
     * ## Y-Axis formating utility functions
     *
     * There are a couple of different ways to format the y-axis labels.
     * Here are a couple of utility y-axis formatting functions.
     */
    Chart.moneyLabelFormatter = function() {
        return '$' + Highcharts.numberFormat(this.value, 0);
    };

    Chart.percentageLabelFormatter = function() {
        return Highcharts.numberFormat(this.value, 0) + '%';
    };

    Chart.numberLabelFormatter = function() {
        if (this.value >= 1000000000) {
            return Highcharts.numberFormat(this.value / 1000000000, 0) + "B";
        } else if (this.value >= 1000000) {
            return Highcharts.numberFormat(this.value / 1000000, 0) + "M";
        } else if (this.value >= 1000) {
            return Highcharts.numberFormat(this.value / 1000, 0) + "K";
        } else if (this.value > 0) {
            return Highcharts.numberFormat(this.value, 0);
        } else {
            return "0";
        }
    };

    /*
     * ## Tooltip Utility functions
     *
     * Like the y-axis formatting, tooltips change depending on the type
     * of data they feature. Here are a couple of common ones.
     */
    Chart.defaultTooltipFormatter = function() {
        var value = Highcharts.numberFormat(this.y, 0);
        var total = Highcharts.numberFormat(this.total, 0);
        var text = '<span style="font-size: 14px;">'
            + Highcharts.dateFormat('%A, %B %e, %Y', this.x)
            + '</span>'
            + '<br/>'
            + '<span style="padding: 0; '
            + 'font-weight: 600; '
            + 'color: ' + this.series.color
            + '">'
            + this.series.name
            + '</span>'
            + ': <strong style="font-weight: 600;">'
            + value
            + '</strong><br/>';
        return text;
    };

    /*
     * ## Chart default options
     */
    Chart.highChartDefaultOptions = {
        chart: {
            defaultSeriesType: 'line',
            margin: [30,0,30,45]
        },
        legend: {
            verticalAlign: "bottom",
            y: -7,
            enabled: true
        },
        yAxis: {
            labels: {
                formatter: Chart.numberLabelFormatter
            }
        },
        tooltip: {
            formatter: Chart.defaultTooltipFormatter
        }
    };

    /*
     * New way of setting up a stats chart. Let's use this.
     */
    Chart.createStatsChart = function(selector, data, extraOptions) {

        // extraOptions aren't required
        if (typeof extraOptions == 'undefined') {
            extraOptions = {};
        }

        // If the data isn't formatted correctly, bring up a chart error
        if (typeof data == 'undefined') {
            Chart.chartError();
            return;
        }

        // Each data item should have a color and a line width
        var colors = ['#0090d9', '#e57300', '#53a600', '#444444', '#60beef'];
        $.each(data, function(iter, item){
            if (typeof item.color == 'undefined') {
                item.color = colors[iter % colors.length];
            }
            item.lineWidth = 4;
        });

        // Create the highcharts options from the
        var options = $.extend(Chart.highChartDefaultOptions, {
            chart: {
                renderTo: selector.replace('#','')
            },
            series: data
        });

        // setup HighCharts chart
        var highchart = new Highcharts.Chart(options);
     };


    /*
     * Old chart stuff. Depricating.
     */
    Chart.insertStatsChart = function(selector, seriesType, data) {
        var metricElement = $(selector);
    };

    Chart.setupDashboardStatsChart = function(seriesType) {
        // get active metric from breakdown
        var metricElement = $('#dashboard-stats .stats-breakdown .active');
        if (metricElement === null || metricElement.length === 0) return;
        var metricElementIdComponents = metricElement.attr('id').split('-');
        var activeMetric = metricElementIdComponents[metricElementIdComponents.length - 1];

        // get data
        var data = mopub.dashboardStatsChartData;
        if (typeof data == 'undefined') {
            Chart.chartError();
            return;
        }

        // set up series
        var colors = ['#0090d9', '#e57300', '#53a600', '#444444'];
        var chartSeries = [];
        var activeData = data[activeMetric];
        if (typeof activeData == 'undefined') {
            Chart.chartError();
            return;
        }

        $.each(activeData, function(i, seriesObject) {
            var seriesName, seriesData, seriesLineWidth;

            $.each(seriesObject, function(name, value) {
                seriesName = name;
                seriesData = value;

                if (seriesType == 'line') {
                    seriesLineWidth = (seriesName == 'MoPub Optimized') ? 3 : 2;
                } else seriesLineWidth = 4;
            });

            chartSeries.push({
                name: seriesName,
                data: seriesData,
                color: colors[i],
                lineWidth: seriesLineWidth
            });
        });

        // setup HighCharts chart
        this.trafficChart = new Highcharts.Chart({
            chart: {
                renderTo: 'dashboard-stats-chart',
                defaultSeriesType: seriesType,
                marginTop: 0,
                marginBottom: 55,
                height: 185

            },
            plotOptions: {
                series: {
                    pointStart: data.pointStart,
                    pointInterval: data.pointInterval
                }
            },
            legend: {
                verticalAlign: "bottom",
                y: -7,
                enabled: (chartSeries.length > 1)
            },
            yAxis: {
                labels: {
                    formatter: function() {
                        if(activeMetric == 'revenue' || activeMetric == 'ecpm') {
                            return '$' + Highcharts.numberFormat(this.value, 0);
                        } else if(activeMetric == 'ctr') {
                            return Highcharts.numberFormat(this.value, 0) + '%';
                        } else {
                            if (this.value >= 1000000000) {
                                return Highcharts.numberFormat(this.value / 1000000000, 0) + "B";
                            } else if (this.value >= 1000000) {
                                return Highcharts.numberFormat(this.value / 1000000, 0) + "M";
                            } else if (this.value >= 1000) {
                                return Highcharts.numberFormat(this.value / 1000, 0) + "K";
                            } else if (this.value > 0) {
                                return Highcharts.numberFormat(this.value, 0);
                            } else {
                                return "0";
                            }
                        }
                        return "0";
                    }
                }
            },
            tooltip: {
                formatter: function() {
                    var text = '', value = '', total = '';

                    if(activeMetric == 'revenue' || activeMetric == 'ecpm') {
                        value = '$' + Highcharts.numberFormat(this.y, 2);
                        total = '$' + Highcharts.numberFormat(this.total, 2) + ' total';
                    } else if (activeMetric == 'clicks') {
                        value = Highcharts.numberFormat(this.y, 0) + ' ' + activeMetric;
                        total = Highcharts.numberFormat(this.total, 0) + ' total ' + activeMetric;
                    } else if (activeMetric == 'ctr') {
                        value = Highcharts.numberFormat(this.y*100, 2) + "% click through";
                        total = "";
                    } else {
                        value = Highcharts.numberFormat(this.y, 0) + ' ' + activeMetric;
                        total = Highcharts.numberFormat(this.total, 0) + ' total ' + activeMetric;
                    }

                    text += '<span style="font-size: 14px;">' + Highcharts.dateFormat('%A, %B %e, %Y', this.x) + '</span><br/>';
                    text += '<span style="padding: 0; font-weight: 600; color: ' + this.series.color + '">' + this.series.name + '</span>' + ': <strong style="font-weight: 600;">' + value + '</strong><br/>';

                    if(chartSeries.length > 1) {
                        text += '<span style="font-size: 12px; color: #666;">';
                        if (this.total > 0 && total) {
                            text += '(' + Highcharts.numberFormat(this.percentage, 0) + '% of ' + total + ')';
                        } else if (total) {
                            text += '(' + total + ')';
                        }
                        text += '</span>';
                    }
                    return text;
                }
            },
            series: chartSeries
        });

        $('#dashboard-stats-chart').removeClass('chart-loading');
     };

    /*
     * ## Pie charts
     * Utility function for creating a pie chart with default options
     */
    Chart.setupPieChart = function (selector, title, chart_data) {

        this.impressionPieChart = new Highcharts.Chart({
            chart: {
                renderTo: selector,
                plotBackgroundColor: null,
                plotShadow: true,
                margin: 0
            },
            title: {
                text: title
            },
            tooltip: {
                formatter: function() {
                    return "<b>"+ this.point.name +"</b>: "+ this.point.total + " " + title;
                }
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: "pointer",
                    dataLabels: {
                        enabled: false,
                        color:  "#000000",
                        connectorColor: "#000000",
                        formatter: function() {
                            return "<b>"+ this.point.name +"</b>: "+ this.percentage.toFixed(2) +" %";
                        }
                    },
                    showInLegend: true
                }
            },
            legend: {
                verticalAlign: "bottom"
            },
            series: [{
                type: "pie",
                name: title,
                data: chart_data
            }]
        });

    };


    Chart.chartError = function() {
        $('#dashboard-stats-chart').removeClass('chart-loading').addClass('chart-error');
    };


    window.Chart = Chart;
    window.Stats = Stats;
    window.mopub = mopub;
    window.mopub.Stats = Stats;
    window.mopub.Chart = Chart;
    window.Mopub = mopub;


})(this.jQuery);


(function($){

    var config = window.ToastjsConfig = {
        defaultTimeOut: 3000,
        position: ["top", "right"],
        notificationStyles: {
            padding: "12px 18px",
            margin: "0 0 6px 0",
            backgroundColor: "#000",
            opacity: 0.8,
            color: "#fff",
            font: "normal 13px 'Droid Sans', sans-serif",
            borderRadius: "3px",
            boxShadow: "#999 0 0 12px",
            width: "300px"
        },
        notificationStylesHover: {
            opacity: 1,
            boxShadow: "#000 0 0 12px"
        },
        container: $("<div></div>")
    };

    $(document).ready(function() {
        config.container.css("position", "absolute");
        config.container.css("z-index", 9999);
        config.container.css(config.position[0], "12px");
        config.container.css(config.position[1], "12px");
        $("body").append(config.container);
    });

    function getNotificationElement() {
        return $("<div>").css(config.notificationStyles).hover(function() {
            $(this).css(config.notificationStylesHover);
        }, function() {
            $(this).css(config.notificationStyles);
        });
    }

    var Toast = window.Toast = {};

    Toast.notify = function(message, title, iconUrl, timeOut) {
        var notificationElement = getNotificationElement();

        timeOut = timeOut || config.defaultTimeOut;

        if (iconUrl) {
            var iconElement = $("<img/>", {
                src: iconUrl,
                css: {
                    width: 36,
                    height: 36,
                    display: "inline-block",
                    verticalAlign: "middle",
                    float: "left"
                }
            });
            notificationElement.append(iconElement);
        }

        var textElement = $("<div/>").css({
            display: 'inline-block',
            verticalAlign: 'middle',
            padding: '0 12px'
        });

        if (title) {
            var titleElement = $("<div/>");
            titleElement.append(document.createTextNode(title));
            titleElement.css("font-weight", "bold");
            textElement.append(titleElement);
        }

        if (message) {
            var messageElement = $("<div/>");
            messageElement.css("width", "230px");
            messageElement.css("float", "left");
            messageElement.html(message);
            textElement.append(messageElement);
        }

        notificationElement.delay(timeOut).fadeOut(function(){
            notificationElement.remove();
        });
        notificationElement.bind("click", function() {
            notificationElement.hide();
        });

        notificationElement.append(textElement);
        config.container.prepend(notificationElement);
    };

    Toast.info = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.warning = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.error = function(message, title) {
        Toast.notify(message, title, "/images/36x36-error.png");
    };

    Toast.success = function(message, title) {
        Toast.notify(message, title, "/images/36x36-success.png");
    };

}(this.jQuery));
var mopub=mopub||{};mopub.Utils=mopub.Utils||{};if(typeof window.console=="undefined"){window.console={log:function(){}}}(function(d){var i=window.mopub||{};var e=window.Chart||{};var b=window.Stats||{};d(document).ready(function(){if(typeof mpq.push!="undefined"){try{d("#dashboard-dateOptions-option-7").click(function(){mpq.push(["track","7 Day Date-option clicked"])});d("#dashboard-dateOptions-option-14").click(function(){mpq.push(["track","14 Day Date-option clicked"])});d("#dashboard-dateOptions-option-30").click(function(){mpq.push(["track","30 Day Date-option clicked"])});d("#dashboard-dateOptions-option-custom").click(function(){mpq.push(["track","Custom Date-option clicked"])});d("#stats-breakdown-dateOptions-option-0").click(function(){mpq.push(["track",'"Today" clicked in Stats Breakdown'])});d("#stats-breakdown-dateOptions-option-1").click(function(){mpq.push(["track",'"Yesterday" clicked in Stats Breakdown'])});d("#stats-breakdown-dateOptions-option-2").click(function(){mpq.push(["track",'"All" clicked in Stats Breakdown'])})}catch(j){}}if(d("#is_admin_input").val()=="False"){d(".marketplace").hide()}var l="/js/libs/jquery-ui-1.8.7.custom/css/mopub/images";d.preLoadImages("/images/ui/ui-button-active.png","/images/ui/ui-button-default.png","/images/ui/ui-button-hover.png","/images/ui/ui-icons-active.png","/images/ui/ui-icons-focus.png","/images/ui/ui-icons-hover.png","/images/ui/ui-icons-progress.png",l+"/ui-bg_highlight-hard_25_e57300_1x100.png",l+"/ui-bg_highlight-hard_50_dddddd_1x100.png",l+"/ui-bg_highlight-hard_100_f3f3f3_1x100.png",l+"/ui-bg_inset-soft_25_595959_1x100.png",l+"/ui-icons_0090d9_256x240.png",l+"/ui-icons_cc2929_256x240.png",l+"/ui-icons_ffffff_256x240.png","/placeholders/image.gif");d("legend").each(function(){var n=d(this);var m=d("<h2>"+n.html()+"</h2>");m.attr("class",n.attr("class"));m.attr("id",n.attr("id"));n.replaceWith(m)});d(".button").button().css({visibility:"visible"});d(".buttonset").buttonset().css({visibility:"visible"});d(".buttonset-start-disabled").buttonset();d(".buttonset-start-disabled").buttonset({disabled:true});d(".selectmenu").selectmenu().css({visibility:"visible"});d(".validate").validate();d(".sortable").tablesorter();d(".tabs").tabs();d(".pills").tabs();d.extend(d.ui.dialog.prototype.options,{modal:true,resizable:false,draggable:false,width:400});d.datepicker.setDefaults({dayNamesMin:["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]});d("input[placeholder], textarea[placeholder]").placeholder({preventRefreshIssues:true});d("#titlebar .breadcrumb h1, .dataTable-name .inner").textOverflow(" &hellip;");d(".dropdown-head").dropdown(".dropdown");d(".alert-message .close").click(function(){d(this).parent().fadeOut()});d.fn.qtip.styles.mopub={background:"#303030",color:"#ffffff",border:{radius:5},tip:{size:{x:10,y:10}},name:"dark"};d("a[title]").qtip({style:{name:"mopub",tip:true}});d(".formFields-field-help-link[title]").click(function(m){m.preventDefault()});function k(){if(d(".messageCenter-message").length===0){d("#messageCenter").hide()}}k();d(".messageCenter-message-moreInfoLink").click(function(o){o.preventDefault();var m=d(this);var n=d(".messageCenter-message-moreInfo",m.parents(".messageCenter-message"));n.clone().dialog({buttons:{Close:function(){d(this).dialog("close")}},close:function(q,p){d(this).remove()}})});d(".messageCenter-message-hide").click(function(o){o.preventDefault();var n=d(this);var m=n.parents(".messageCenter-message");m.fadeOut("fast",function(){m.remove();k()})});Highcharts.setOptions({chart:{animation:false,backgroundColor:null,borderRadius:0,margin:[30,0,30,45],height:185},title:{text:null},lang:{loading:"Loading ..."},credits:{enabled:false},style:{fontFamily:'"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif'},plotOptions:{series:{animation:false,shadow:false,stickyTracking:false},area:{lineWidth:4,fillOpacity:0.1,stacking:"normal",marker:{lineWidth:2,radius:5,symbol:"circle",states:{hover:{lineWidth:2,radius:7}}},states:{hover:{lineWidth:4}}}},xAxis:{endOnTick:false,gridLineWidth:0.5,gridLineColor:"#dddddd",lineWidth:1,lineColor:"#cccccc",type:"datetime",labels:{style:{fontFamily:'"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',color:"#999",fontSize:"10px"},y:20},dateTimeLabelFormats:{second:"%b %e %l:%M:%S%p",minute:"%b %e %l:%M%p",hour:"%b %e %l:%M%p",day:"%b %e",week:"%b %e",month:"%b %Y",year:"%Y"},tickColor:"#dddddd",tickLength:5,tickWidth:0.5},yAxis:{showFirstLabel:false,showLastLabel:true,gridLineWidth:0.5,gridLineColor:"#dddddd",min:0,title:{text:null},labels:{style:{fontFamily:'"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',color:"#999",fontSize:"10px"},x:-5}},legend:{borderColor:null,borderRadius:0,borderWidth:0,align:"center",verticalAlign:"top",y:-17,itemStyle:{fontFamily:'"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',size:"12px",cursor:"pointer",color:"#444444"},itemHoverStyle:{color:"#e57300"},itemHiddenStyle:{color:"#ccc"},lineHeight:12,symbolPadding:6,symbolWidth:12},tooltip:{backgroundColor:"rgba(255, 255, 255, .9)",style:{fontFamily:'"myriad-pro-1", "myriad-pro-2", Helvetica, Arial, sans-serif',fontSize:"13px",padding:"10px"}}});d(".whatsthis").live("click",function(m){m.preventDefault();d("#"+d(this).attr("id").replace("helpLink","helpContent")).dialog({buttons:{Close:function(){d(this).dialog("close")}}})})});function g(){var l={};var j=window.location.search.slice(1).split("&");var m;for(var k=0;k<j.length;k++){m=j[k].split("=");l[m[0]]=m[1]}return l}var f=g();var a=[];d.preLoadImages=function(){var l=arguments.length;for(var k=l;k--;){var j=document.createElement("img");j.src=arguments[k];a.push(j)}};d.fn.dropdown=function(j){var k=this;var n,m=false;o();function l(){if(d(j).hasClass("invisible")){}d(j).removeClass("invisible");d(k).addClass("hovered")}function o(){if(!d(j).hasClass("invisible")){d(j).addClass("invisible")}d(k).removeClass("hovered")}d(this).hover(function(){n=true},function(){n=false});d(j).hover(function(){m=true},function(){m=false});setInterval(function(){if(n||m){l()}else{o()}},1)};function h(j){return j.hasClass("active")}function c(k,j){if(j.length>1){j.each(function(){d(this).removeClass("active")})}else{j.find(".active").removeClass("active")}k.addClass("active")}d.fn.tabs=function(){var k=d(".tab-section");var l=d(this);var j=d("li",l);d.each(j,function(m,p){var o=d("a",p);d(o).click(function(q){q.preventDefault()});var n=o.attr("href");d(p).click(function(){c(d(this),l);c(d(n),k);window.location.hash=n+"-tab"});if(window.location.hash==n+"-tab"){d(p).click()}})};d.unescapeHTML=function(j){return d("<div />").html(j).text()};d.escapeHTML=function(j){return d("<div />").text(j).html()};d.fn.lightswitch=function(m,k){if(typeof m=="undefined"){m=function(){return true}}if(typeof k=="undefined"){k=function(){return true}}var j=d(this);var l=d(".switch",j);j.click(function(){if(l.hasClass("on")){var n=k();if(n){l.removeClass("on").addClass("off")}}else{if(l.hasClass("off")){var n=m();if(n){l.removeClass("off").addClass("on")}}else{l.addClass("off")}}})};d.fn.lightswitchOn=function(){var j=d(this);var k=d(".switch",j);k.removeClass("off").addClass("on")};d.fn.lightswitchOff=function(){var j=d(this);var k=d(".switch",j);k.removeClass("on").addClass("off")};i.Utils=i.Utils||{};i.Utils.formatNumberWithCommas=function(n){n+="";var j=n.split(".");var m=j[0];var k=j.length>1?"."+j[1]:"";var l=/(\d+)(\d{3})/;while(l.test(m)){var m=m.replace(l,"$1,$2")}return m+k};i.Utils.formatCurrency=function(j){return"$"+i.Utils.formatNumberWithCommas(j.toFixed(2))};i.Utils.formatNumberAsPercentage=function(j){return(j*100).toFixed(2)+"%"};i.Utils.getKeysFromObject=function(j){var l=[];for(var k in j){if(j.hasOwnProperty(k)){l.push(k)}}return l};b.sortStatsObjectsByStat=function(k,j){k.sort(function(m,l){var o=parseFloat(m.stats["sum"][j]);var n=parseFloat(l.stats["sum"][j]);if(o<n){return 1}if(o>n){return -1}else{return 0}});return k};b.statArrayFromDailyStats=function(k,j){return d.map(k,function(l){return parseFloat(l[j])})};b.getGraphSummedStatsForStatName=function(k,n){var j=[];var p=n.splice(0,3);var m=n;d.each(p,function(s,q){var r=q.key;var u=q.stats["daily_stats"];var t={};t[r]=b.statArrayFromDailyStats(u,k);j.push(t)});if(m.length==0){return j}var l=b.sumDailyStatsAcrossStatsObjects(m,k);var o={Others:l};j.push(o);return j};b.sumDailyStatsAcrossStatsObjects=function(l,k){var j=[];d.each(l,function(n,m){var o=m.stats["daily_stats"];d.each(o,function(q,p){if(!j[q]){j[q]=0}j[q]+=parseFloat(p[k])})});return j};b.getGraphCtrStats=function(m){var j=[];var o=m.splice(0,3);var l=m;d.each(o,function(r,p){var q=p.key;var t=p.stats["daily_stats"];var s={};s[q]=b.statArrayFromDailyStats(t,"ctr");j.push(s)});if(l.length==0){return j}var k=b.getDailyCtrAcrossStatsObjects(l);var n={Others:k};j.push(n);return j};b.getDailyCtrAcrossStatsObjects=function(n){var m=[];var l=b.sumDailyStatsAcrossStatsObjects(n,"click_count");var o=b.sumDailyStatsAcrossStatsObjects(n,"impression_count");for(var k=0,j=l.length;k<j;k++){m[k]=(o[k]===0)?0:l[k]/o[k]}return m};e.moneyLabelFormatter=function(){return"$"+Highcharts.numberFormat(this.value,0)};e.percentageLabelFormatter=function(){return Highcharts.numberFormat(this.value,0)+"%"};e.numberLabelFormatter=function(){if(this.value>=1000000000){return Highcharts.numberFormat(this.value/1000000000,0)+"B"}else{if(this.value>=1000000){return Highcharts.numberFormat(this.value/1000000,0)+"M"}else{if(this.value>=1000){return Highcharts.numberFormat(this.value/1000,0)+"K"}else{if(this.value>0){return Highcharts.numberFormat(this.value,0)}else{return"0"}}}}};e.defaultTooltipFormatter=function(){var k=Highcharts.numberFormat(this.y,0);var j=Highcharts.numberFormat(this.total,0);var l='<span style="font-size: 14px;">'+Highcharts.dateFormat("%A, %B %e, %Y",this.x)+'</span><br/><span style="padding: 0; font-weight: 600; color: '+this.series.color+'">'+this.series.name+'</span>: <strong style="font-weight: 600;">'+k+"</strong><br/>";return l};e.highChartDefaultOptions={chart:{defaultSeriesType:"line",margin:[30,0,30,45]},legend:{verticalAlign:"bottom",y:-7,enabled:true},yAxis:{labels:{formatter:e.numberLabelFormatter}},tooltip:{formatter:e.defaultTooltipFormatter}};e.createStatsChart=function(j,o,m){if(typeof m=="undefined"){m={}}if(typeof o=="undefined"){e.chartError();return}var k=["#0090d9","#e57300","#53a600","#444444","#60beef"];d.each(o,function(p,q){if(typeof q.color=="undefined"){q.color=k[p%k.length]}q.lineWidth=4});var l=d.extend(e.highChartDefaultOptions,{chart:{renderTo:j.replace("#","")},series:o});var n=new Highcharts.Chart(l)};e.insertStatsChart=function(j,l,m){var k=d(j)};e.setupDashboardStatsChart=function(l){var k=d("#dashboard-stats .stats-breakdown .active");if(k===null||k.length===0){return}var q=k.attr("id").split("-");var m=q[q.length-1];var n=i.dashboardStatsChartData;if(typeof n=="undefined"){e.chartError();return}var j=["#0090d9","#e57300","#53a600","#444444"];var o=[];var p=n[m];if(typeof p=="undefined"){e.chartError();return}d.each(p,function(u,v){var r,t,s;d.each(v,function(w,x){r=w;t=x;if(l=="line"){s=(r=="MoPub Optimized")?3:2}else{s=4}});o.push({name:r,data:t,color:j[u],lineWidth:s})});this.trafficChart=new Highcharts.Chart({chart:{renderTo:"dashboard-stats-chart",defaultSeriesType:l,marginTop:0,marginBottom:55,height:185},plotOptions:{series:{pointStart:n.pointStart,pointInterval:n.pointInterval}},legend:{verticalAlign:"bottom",y:-7,enabled:(o.length>1)},yAxis:{labels:{formatter:function(){if(m=="revenue"||m=="ecpm"){return"$"+Highcharts.numberFormat(this.value,0)}else{if(m=="ctr"){return Highcharts.numberFormat(this.value,0)+"%"}else{if(this.value>=1000000000){return Highcharts.numberFormat(this.value/1000000000,0)+"B"}else{if(this.value>=1000000){return Highcharts.numberFormat(this.value/1000000,0)+"M"}else{if(this.value>=1000){return Highcharts.numberFormat(this.value/1000,0)+"K"}else{if(this.value>0){return Highcharts.numberFormat(this.value,0)}else{return"0"}}}}}}return"0"}}},tooltip:{formatter:function(){var t="",s="",r="";if(m=="revenue"||m=="ecpm"){s="$"+Highcharts.numberFormat(this.y,2);r="$"+Highcharts.numberFormat(this.total,2)+" total"}else{if(m=="clicks"){s=Highcharts.numberFormat(this.y,0)+" "+m;r=Highcharts.numberFormat(this.total,0)+" total "+m}else{if(m=="ctr"){s=Highcharts.numberFormat(this.y*100,2)+"% click through";r=""}else{s=Highcharts.numberFormat(this.y,0)+" "+m;r=Highcharts.numberFormat(this.total,0)+" total "+m}}}t+='<span style="font-size: 14px;">'+Highcharts.dateFormat("%A, %B %e, %Y",this.x)+"</span><br/>";t+='<span style="padding: 0; font-weight: 600; color: '+this.series.color+'">'+this.series.name+'</span>: <strong style="font-weight: 600;">'+s+"</strong><br/>";if(o.length>1){t+='<span style="font-size: 12px; color: #666;">';if(this.total>0&&r){t+="("+Highcharts.numberFormat(this.percentage,0)+"% of "+r+")"}else{if(r){t+="("+r+")"}}t+="</span>"}return t}},series:o});d("#dashboard-stats-chart").removeClass("chart-loading")};e.setupPieChart=function(j,k,l){this.impressionPieChart=new Highcharts.Chart({chart:{renderTo:j,plotBackgroundColor:null,plotShadow:true,margin:0},title:{text:k},tooltip:{formatter:function(){return"<b>"+this.point.name+"</b>: "+this.point.total+" "+k}},plotOptions:{pie:{allowPointSelect:true,cursor:"pointer",dataLabels:{enabled:false,color:"#000000",connectorColor:"#000000",formatter:function(){return"<b>"+this.point.name+"</b>: "+this.percentage.toFixed(2)+" %"}},showInLegend:true}},legend:{verticalAlign:"bottom"},series:[{type:"pie",name:k,data:l}]})};e.chartError=function(){d("#dashboard-stats-chart").removeClass("chart-loading").addClass("chart-error")};window.Chart=e;window.Stats=b;window.mopub=i;window.mopub.Stats=b;window.mopub.Chart=e;window.Mopub=i})(this.jQuery);
$(function() {
    // TODO: document
    /*
     *   adgroups_data
     *   graph_start_date
     *   today
     *   yesterday
     *   ajax_query_string
     */

    var toast_error = function () {
         var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

    var NetworksController = {

        initialize: function(bootstrapping_data) {
            var adgroups_data = bootstrapping_data.adgroups_data,
                graph_start_date = bootstrapping_data.graph_start_date,
                today = bootstrapping_data.today,
                yesterday = bootstrapping_data.yesterday,
                ajax_query_string = bootstrapping_data.ajax_query_string;

            var adgroups = new AdGroups(adgroups_data);

            var graph_view = new CollectionGraphView({
                collection: adgroups,
                start_date: graph_start_date,
                today: today,
                yesterday: yesterday
            });
            graph_view.render();

            var adgroups_view = new AdGroupsView({
                collection: adgroups,
                el: '#adgroups',
                title: 'Ad Networks',
                type: 'network'
            });
            adgroups_view.render();

            adgroups.each(function(adgroup) {
                adgroup.fetch({
                    data: ajax_query_string,
                    error: function () {
                        adgroup.fetch({
                            error: toast_error
                        });
                    }
                });
            });

            // TODO: move to views
            // date picker
            // set up dateOptions
            $('#dashboard-dateOptions input').click(function() {
                var option = $(this).val();
                    var hash = document.location.hash;
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
                                    var num_days=Math.round((to_date.getTime()-from_date.getTime())/(86400000));

                                    var from_day=from_date.getDate();
                                    var from_month=from_date.getMonth()+1;
                                    var from_year=from_date.getFullYear();

                                    $(this).dialog("close");
                                    var location = document.location.href.replace(hash, '').replace(/\?.*/,'');
                                    document.location.href = location+'?r='+num_days+'&s='+from_year+"-"+from_month+"-"+from_day + hash;
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
                } else {
                    // Tell server about selected option to get new data
                    var location = document.location.href.replace(hash,'').replace(/\?.*/,'');
                    document.location.href = location+'?r=' + option + hash;
                }
            });


            // set up custom dateOptions modal dialog
            $('#dashboard-dateOptions-custom-from').datepicker({
                defaultDate: '-15d',
                maxDate: '0d',
                    onSelect: function(selectedDate) {
                        var other = $('#dashboard-dateOptions-custom-to');
                        var instance = $(this).data("datepicker");
                        var date = $.datepicker.parseDate(instance.settings.dateFormat ||
                                                          $.datepicker._defaults.dateFormat,
                                                          selectedDate,
                                                          instance.settings);
                        other.datepicker('option', 'minDate', date);
                    }
        });

            $('#dashboard-dateOptions-custom-to').datepicker({
                defaultDate: '-1d',
                maxDate: '0d',
                onSelect: function(selectedDate) {
                    var other = $('#dashboard-dateOptions-custom-from');
                    var instance = $(this).data("datepicker");
                    var date = $.datepicker.parseDate(instance.settings.dateFormat ||
                                                      $.datepicker._defaults.dateFormat,
                                                      selectedDate,
                                                      instance.settings);
                    other.datepicker('option', 'maxDate', date);
                }
            });

            var self = this;
            // stats breakdown
            $('.stats-breakdown tr').click(function(e) {
                var row = $(this);
                if(!row.hasClass('active')) {
                    row.siblings().removeClass('active');
                    row.addClass('active');
                    $('#dashboard-stats-chart').fadeOut(100, function() {
                        graph_view.show_chart();
                        $(this).show();
                    });
                }
            });

            $('#stats-breakdown-dateOptions input').click(function() {
                $('.stats-breakdown-value').hide();
                $('.stats-breakdown-value.'+$(this).val()).show();
            });

            $('.stats-breakdown-value').hide();
            $('.stats-breakdown-value.all').show();

            // Ad Campaign button
            $("#add_campaign_button").button({
                icons : { primary : 'ui-icon-circle-plus'}
            });


            // AdGroups form
            var actions = ['pause', 'resume', 'activate', 'archive', 'delete'];
            $.each(actions, function(iter, action) {
                $('#campaignForm-' + action).click(function(e) {
                    e.preventDefault();
                    $('#campaignForm')
                        .find("#action")
                        .attr("value", action)
                        .end()
                        .submit();
                });
            });
        }
    };

    window.NetworksController = NetworksController;
});

/*
	MoPub Public Site JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
	// dom ready
	$(document).ready(function() {

		/*---------------------------------------/
		/ UI
		/---------------------------------------*/

		// Header icons
		$('#header-icons a').css({ opacity: 0.25 }).hover(function() {
			$(this).stop().animate({ opacity: 0.75 }, 200);
		}, function() {
			$(this).stop().animate({ opacity: 0.25 }, 400);
		});

	});
})(this.jQuery);
/*
 * # MoPub Publisher/Inventory Javascript
 * ## Client-side functionality for the following pages:
 * * Inventory/Dashboard
 * * App detail
 * * Adunit detail
 * * App creation
 * * Sign up flow
 * * Geographical targeting (deprecated)
 */

var mopub = mopub || {};

(function($, Backbone, _){

    /*
     * ## Helpers for DashboardController
     */

    var toast_error = function () {
        var message = $("Please <a href='#'>refresh the page</a> and try again.")
            .click(function(e){
                e.preventDefault();
                window.location.reload();
            });
        Toast.error(message, "Error fetching app data.");
    };

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
     * ## fetchAppStats
     * Fetches all app stats using a list of app keys and renders
     * them into table rows that have already been created in the
     * page. Useful for decreasing page load time along with `fetchAdunitStats`.
     */
    function fetchAppStats (app_keys) {
        _.each(app_keys, function(app_key) {
            var app = new App({id: app_key, stats_endpoint: 'all'});
            app.bind('change', function(current_app) {
                var appView = new AppView({ model: current_app, el: '#dashboard-apps' });
                appView.renderInline();
            });
            app.fetch({
                error: function() {
                    app.fetch({
                        error: toast_error
                    });
                }
            });
        });
    }

    /*
     * ## fetchAdunitStats
     * Fetches AdUnit stats for an app over ajax and renders them in already
     * existing table rows. This method is useful for decreasing page load time.
     * Uses a parent app's key to bootstrap the fetch.
     */
    function fetchAdunitStats (app_key) {
        var adunits = new AdUnitCollection();
        adunits.app_id = app_key;
        adunits.stats_endpoint = 'all';
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
            },
            error: function () {
                adunits.fetch({
                    error: toast_error
                });
            }
        });
    }


    /*
     * ## initializeNewAppForm
     * Loads all click handlers/visual stuff/ajax loading for
     * the app form.
     */
    function initializeNewAppForm() {

        initializeiOSAppSearch();

        $('#appForm-submit')
            .button({
                icons: { secondary: "ui-icon-circle-triangle-e" }
            })
            .click(function(e) {
                e.preventDefault();
                $('#appForm').submit();
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
                script.src = 'http://ax.itunes.apple.com'
                    + '/WebObjects/MZStoreServices.woa/wa/wsSearch'+
                    + '?entity=software&limit=10&callback=loadedArtwork&term='
                    + name;
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
            } else {
                $('#appForm-search-button').button("disable");
                $('#appForm-market-search-button').button('disable');
            }
            if (e.keyCode == 13) {
                if (type == 'iphone') {
                    $('#appForm-search-button').click();
                } else if (type == 'android') {
                    $('#appForm-market-search-button').click();
                }
            }
        });

        $('#appForm-changeIcon-link').click(function (e) {
            e.preventDefault();
            $(this).hide();
            $('#appForm-icon-upload').show();
            $('#appForm input[name="img_url"]').val('');
        });

        $('input[name="app_type"]').click(function(e) {
            $('#appForm .appForm-platformDependent')
                .removeClass('iphone')
                .removeClass('android')
                .removeClass('mweb')
                .addClass($(this).val());
        }).filter(':checked').click(); // make sure we're in sync when the page Loads
    }

    function initializeEditAppForm() {
        // Set up all of the handlers from the new app form for the new
        // app form.
        initializeNewAppForm();

        // Handler for submitting the edit app form over ajax.
        // If the form submit is successful, the page will reload.
        // If not, the errors will eb displayed.
        $('#appForm.appEditForm').ajaxForm({
            data: { ajax: true },
            dataType: 'json',
            success: function(jsonData, statusText, xhr, $form) {

                // Hide the loading spinner
                $('#appEditForm-loading').hide();

                // Reload the page if the form save was successful
                if (jsonData.success) {
                    window.location.reload();
                } else {
                    // Remove the existing errors before we add the new ones.
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
                    initializeNewAppForm();
                    window.location.hash = '';
                    window.location.hash = 'appForm';
                }
            }
        });

        // When the 'submit' button is clicked, show the loading spinner
        // and submit the form.
        $('#appEditForm-submit')
            .button({
                icons: { secondary: "ui-icon-circle-triangle-e" }
            })
            .click(function(e) {
                e.preventDefault();
                $('#appEditForm-loading').show();
                $('#appForm').submit();
            });

        // When the 'cancel' button is clicked, hide the form by sliding it up
        $('#appEditForm-cancel')
            .click(function(e) {
                e.preventDefault();
                $('#dashboard-appEditForm').slideUp('fast');
            });

        // When the 'edit app settings' button is click, hide/show the app form
        $('#dashboard-apps-editAppButton')
            .button({
                icons: { primary: "ui-icon-wrench" }
            })
            .click(function(e) {
                e.preventDefault();
                if ($('#dashboard-appEditForm').is(':visible')) {
                    $('#dashboard-appEditForm').slideUp('fast');
                } else {
                    $('#dashboard-appEditForm').slideDown('fast');
                }
            });
    }

    /*
     * ## initializeNewAdunitForm
     * Loads all click handlers/visual stuff/ajax loading for
     * the app form.
     */
    function initializeNewAdunitForm() {

        // Set up device format selection UI
        $("#adunit-device_format_phone")
            .parent()
            .buttonset();

        $("#adunit-device_format_phone")
            .click(function(e){
                $('#adForm-tablet-container').hide();
                $('#adForm-phone-container')
                    .show()
                    .find('input[type="radio"]')[0].click();
            });

        // Click handler for the tablet format
        $('#adunit-device_format_tablet').click(function(e){
            console.log('tablet clicked');
            $('#adForm-phone-container').hide();
            $('#adForm-tablet-container')
                .show()
                .find('input[type="radio"]')[0].click();
        });

        // Slide up/down handler for the form div
        $('#dashboard-apps-addAdUnitButton')
            .button({
                icons: { primary: "ui-icon-circle-plus" }
            })
            .click(function(e) {
                e.preventDefault();
                if ($('#dashboard-adunitAddForm').is(':visible'))
                    $('#dashboard-adunitAddForm').slideUp('fast');
                else
                    $('#dashboard-adunitAddForm').slideDown('fast');
            });

        // Submitting over ajax
        $('#adunitAddForm-submit')
            .button({
                icons: { secondary: "ui-icon-circle-triangle-e" }
            })
            .click(function(e) {
                e.preventDefault();
                $('#adunitForm-loading').show();
                $('#adunitAddForm').submit();
            });

        // Cancel button that hides the form
        $('#adunitAddForm-cancel')
            .click(function(e) {
                e.preventDefault();
                $('#dashboard-adunitAddForm').slideUp('fast', function() {
                    $('#dashboard-apps-addAdUnitButton').show();
                });
            });

        $('#adunitAddForm').ajaxForm({
            data: { ajax: true },
            dataType: 'json',
            success: function(jsonData, statusText, xhr, $form) {
                $('#adunitForm-loading').hide();
                if (jsonData.success) {
                    window.location.reload();
                } else {
                    // reimplement the onload event
                    initializeNewAppForm();
                    initializeNewAdunitForm();
                    window.location.hash = '';
                    window.location.hash = 'adunitForm';
                }
            }
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
                } else {
                    $full_onlys.hide();
                    $banner_onlys.show();
                }

                var $custom_onlys = $(".custom_only");
                if ($(this).attr("id") == "appForm-adUnitFormat-tablet-custom" ||
                    $(this).attr("id") == "appForm-adUnitFormat-custom") {
                    $custom_onlys.show();
                } else {
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
            $(this).find('input[type="radio"]').click(function(e) {
                var index = $(this).parent().index();
                var images = $("#adForm-images-container");
                images.children().hide();
                var image = images.children()[index];
                $(image).show().css({ opacity: 1 });

                var $full_onlys = $(".full_only");
                var $banner_onlys = $(".banner_only");
                if ($(this).attr("id") == "appForm-adUnitFormat-full-tablet" ||
                    $(this).attr("id") == "appForm-adUnitFormat-full"){
                    $full_onlys.show();
                    $banner_onlys.hide();
                } else {
                    $full_onlys.hide();
                    $banner_onlys.show();
                }

                var $custom_onlys = $(".custom_only");
                if ($(this).attr("id") == "appForm-adUnitFormat-tablet-custom" ||
                    $(this).attr("id") == "appForm-adUnitFormat-custom"){
                    $custom_onlys.show();
                } else {
                    $custom_onlys.hide();
                }

            }).first().click(); //initialize by activating the first
        });

        //initialize checked elements
        $("#adunit-device_format_phone").parent().children()
            .filter(':checked')
            .click()
            .each(function() {
                var deviceFormat = $(this).val(); //either tablet or phone
                var container = "#adForm-" + deviceFormat + "-container";
                $(container).find('.possible-format').click();
            });
        }


    /*
     * ## initializeEditAdunitForm
     * Like the app editing form, the adunit editing form is done
     * over ajax and is displayed in div that slides in and out of
     * the page.
     */
    function initializeEditAdunitForm() {

        initializeNewAdunitForm();

        $('#dashboard-apps-editAdUnitButton')
            .button({ icons: { primary: "ui-icon-wrench" } })
            .click(function(e) {
                e.preventDefault();
                if ($('#dashboard-adunitEditForm').is(':visible'))
                    $('#dashboard-adunitEditForm').slideUp('fast');
                else
                    $('#dashboard-adunitEditForm').slideDown('fast');
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

        $('#adunitAddForm').ajaxForm({
            data: {
                ajax: true
            },
            dataType: 'json',
            success: function(jsonData, statusText, xhr, $form) {
                $('#adunitForm-loading').hide();
                if (jsonData.success) {
                    window.location.reload();
                } else {

                    // reimplement the onload event
                    initializeNewAppForm();
                    initializeNewAdunitForm();
                    window.location.hash = '';
                    window.location.hash = 'adunitForm';
                }
            }
        });
    }

    /*
     * ## initializeDailyCounts
     * Initializes click handlers in the daily counts section for the
     * app/adunit detail pages.
     */
    function initializeDailyCounts() {

        var button = $('.appData-details-toggleButton');
        button.button();

        var individual_daily_counts = $("#appData-individual");

        button.click(function(e) {
            e.preventDefault();
            if (individual_daily_counts.hasClass("hidden")) {
                individual_daily_counts.removeClass("hidden");
                button.button('option', 'label', 'Hide Details');
            } else {
                individual_daily_counts.addClass("hidden");
                button.button('option', 'label', 'Show Details');
                button.button();
            }
        });

    }


    /*
     * ## initializeDateButtons
     * Loads all click handlers/visual stuff for the date buttons. Used
     * on a ton of pages, probably could be refactored by someone brave
     * enough.
     */
    function initializeDateButtons () {
        $('#dashboard-dateOptions input').click(function() {
            var option = $(this).val();
            if (option == 'custom') {
                $('#dashboard-dateOptions-custom-modal').dialog({
                    width: 570,
                    buttons: [
                        {
                            text: 'Set dates',
                            css: { fontWeight: '600' },
                            click: function() {
                                var from_date = $('#dashboard-dateOptions-custom-from').datepicker("getDate");
                                var to_date = $('#dashboard-dateOptions-custom-to').datepicker("getDate");
                                var num_days = Math.ceil((to_date.getTime()-from_date.getTime())/(86400000)) + 1;

                                var from_day = from_date.getDate();
                                // FYI, months are indexed from 0
                                var from_month = from_date.getMonth() + 1;
                                var from_year = from_date.getFullYear();

                                $(this).dialog("close");
                                var location = document.location.href.replace(/\?.*/,'');
                                document.location.href = location
                                    + '?r=' + num_days
                                    + '&s=' + from_year + "-" + from_month + "-" + from_day;
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
            } else {
                // Tell server about selected option to get new data
                var location = document.location.href.replace(/\?.*/,'');
                document.location.href = location + '?r=' + option;
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
                var date = $.datepicker.parseDate(instance.settings.dateFormat
                                                  || $.datepicker._defaults.dateFormat,
                                                  selectedDate,
                                                  instance.settings);
                other.datepicker('option', 'minDate', date);
            }
        });

        $('#dashboard-dateOptions-custom-to').datepicker({
            defaultDate: '-1d',
            maxDate: '0d',
            onSelect: function(selectedDate) {
                var other = $('#dashboard-dateOptions-custom-from');
                var instance = $(this).data("datepicker");
                var date = $.datepicker.parseDate(instance.settings.dateFormat ||
                                                  $.datepicker._defaults.dateFormat,
                                                  selectedDate,
                                                  instance.settings);
                other.datepicker('option', 'maxDate', date);
            }
        });
    }

    /*
     * ## initializeDeleteForm
     * Deleting apps/adunits is done with a form that's submitted via a dialog.
     * The ajax submitting of the form and the dialog popup are done here.
     */
    function initializeDeleteForm() {
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
    }

    /*
     * ## initializeiOSAppSearch
     * Sets up the iTunes app store searching functionality for creating new apps.
     */
    function initializeiOSAppSearch() {
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
                script.src = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch?'
                    + 'entity=software&limit=10&callback=loadedArtwork&term='
                    + name;
                var head = document.getElementsByTagName("head")[0];
                (head || document.body).appendChild( script );
            });
    }

    /*
     * # initializeCommon
     * This function groups together a couple of pieces of functionality that are used on
     * all of the publisher pages (inventory, app, adunit stuff)
     */
    function initializeCommon() {
        initializeDateButtons();
        // Use breakdown to switch charts
        $('.stats-breakdown tr').click(function(e) {
            $('#dashboard-stats-chart').fadeOut(100, function() {
                mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());
                $(this).show();
            });
        });

        $('.stats-breakdown tr').click(function(e) {
            var row = $(this);
            if (!row.hasClass('active')) {
                var table = row.parents('table');
                $('tr.active', table).removeClass('active');
                row.addClass('active');
            }
        });

        $('.appData-id').each(function() {
            var id = $(this);
            var td = id.parents('tr');
            td.hover(
                function() {
                    id.show();
                },
                function() {
                    id.hide();
                });
        });
    }

    function fetchAppsForAdgroup(adgroup_key) {
        // fill in
    }

    /*
     * ## Dashboard Controller
     */
    var DashboardController = {
        initializeIndex: function (bootstrapping_data) {

            // Adds click handlers for the top date buttons and stats breakdown
            // date buttons, and click handlers for the stats breakdown graph-
            // changing
            initializeCommon();

            // Populate the graph
            populateGraphWithAccountStats(bootstrapping_data.account_stats,
                                          bootstrapping_data.start_date);

            // Populate the app/adunit stats table
            fetchAppStats(bootstrapping_data.app_keys);
            _.each(bootstrapping_data.app_keys, function(app_key) {
                fetchAdunitStats(app_key);
            });

            // Add icon to the 'Add an app' button
            // Remove later with new button treatment
            $('#dashboard-apps-addAppButton')
                .button({ icons: { primary: "ui-icon-circle-plus" } });

            // Do Dashboard export
            $('#publisher-dashboard-exportSelect')
                .change(function(e) {
                    e.preventDefault();
                    var val = $(this).val();
                    if (val != 'exp') {
                        $('#dashboardExportForm')
                .find('#appExportType')
                            .val(val)
                            .end()
                            .submit();
                    }
                    $(this).selectmenu('index', 0);
                });


            // Hide unneeded li entry
            $('#publisher-dashboard-exportSelect-menu').find('li').first().hide();

        },
        initializeGeo: function (bootstrapping_data) {
            initializeCommon();
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());

        },

        initializeAppDetail: function (bootstrapping_data) {
            initializeCommon();
            initializeEditAppForm();
            initializeNewAdunitForm();
            initializeDeleteForm();
            initializeiOSAppSearch();
            initializeDailyCounts();
            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());

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

            fetchAppStats([bootstrapping_data.app_key]);
            fetchAdunitStats(bootstrapping_data.app_key);
        },

        initializeAdunitDetail: function (bootstrapping_data) {
            initializeCommon();
            initializeDeleteForm();
            initializeDailyCounts();
            initializeEditAdunitForm();

            mopub.Chart.setupDashboardStatsChart(getCurrentChartSeriesType());

            $('#advertisers-testAdServer')
                .button({ icons : {secondary : 'ui-icon-circle-triangle-e'} })
                .click(function(e) {
                    e.preventDefault();
                    $('#adserverTest').dialog({
                        buttons: {
                            "Close": function() {
                                $(this).dialog("close");
                            }
                        }
                    });
                    $('#adserverTest-iFrame').attr('src',$('#adserverTest-iFrame-src').text());
                });
        },

        initializeAppCreate: function (bootstrapping_data) {
            initializeCommon();
            initializeNewAppForm();
            initializeNewAdunitForm();
        }
    };

    window.DashboardController = DashboardController;


})(this.jQuery, this.Backbone, this._);


/* REFACTOR */
var artwork_json;

// fuck you
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

        $('#searchAppStore-results')
            .append($("<div class='adForm-appSearch' />")
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
                                    .append($("<a href=\"#\" onclick=\"selectArtwork("+i
                                              +");return false\";>"+app['trackName']+"</a>"))
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
                              .append($("<span />")) );
}

var mopub=mopub||{};(function(h,b,r){function a(){var s=h("#dashboard-stats .stats-breakdown .active");if(s.attr("id")=="stats-breakdown-ctr"){return"line"}else{return"area"}}function e(t,s){var u=t.all_stats["||"]["daily_stats"];mopub.dashboardStatsChartData={pointStart:s,pointInterval:86400000,requests:[{Total:mopub.Stats.statArrayFromDailyStats(u,"request_count")}],impressions:[{Total:mopub.Stats.statArrayFromDailyStats(u,"impression_count")}],clicks:[{Total:mopub.Stats.statArrayFromDailyStats(u,"click_count")}],users:[{Total:mopub.Stats.statArrayFromDailyStats(u,"user_count")}]};mopub.Chart.setupDashboardStatsChart(a())}function i(s){r.each(s,function(t){var u=new App({id:t,stats_endpoint:"all"});u.bind("change",function(v){var w=new AppView({model:v,el:"#dashboard-apps"});w.renderInline()});u.fetch()})}function k(t){var s=new AdUnitCollection();s.app_id=t;s.stats_endpoint="all";s.bind("reset",function(u){r.each(u.models,function(v){var w=new AdUnitView({model:v,el:"#dashboard-apps"});w.renderInline()})});s.fetch({success:function(u){h("table").trigger("update");h("#"+t+"-img").hide()}})}function l(){q();h("#appForm-submit").button({icons:{secondary:"ui-icon-circle-triangle-e"}}).click(function(s){s.preventDefault();h("#appForm").submit()});h('#appForm input[name="app_type"]').click(function(s){h("#appForm .appForm-platformDependent").removeClass("iphone").removeClass("android").addClass(h(this).val())}).filter(":checked").click();h('input[name="name"]').change(function(){var s=h.trim(h(this).val());h("#appForm-adUnitName").val(s+" banner ad")});h("#appForm-search-button").button({icons:{primary:"ui-icon-search"}}).click(function(v){v.preventDefault();if(h(this).button("option","disabled")){return}h("#searchAppStore-loading").show();h("#dashboard-searchAppStore-custom-modal").dialog({buttons:[{text:"Cancel",click:function(){h("#searchAppStore-results").html("");h(this).dialog("close")}}]});var t=h('#appForm input[name="name"]').val();var s=document.createElement("script");s.src="http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch"+ +"?entity=software&limit=10&callback=loadedArtwork&term="+t;var u=document.getElementsByTagName("head")[0];(u||document.body).appendChild(s)});if(h("#appForm-name").val()===""){h("#appForm-search-button").button("disable");h("#appForm-search").button("disable");h("#appForm-market-search-button").button("disable");h("#appForm-market-search").button("disable")}h("#appForm-name").keyup(function(u){var s=h.trim(h(this).val());var t=h('input:radio[name="app_type"]:checked').val();if(s.length){h("#appForm-search-button").button("enable");h("#appForm-market-search-button").button("enable")}else{h("#appForm-search-button").button("disable");h("#appForm-market-search-button").button("disable")}if(u.keyCode==13){if(t=="iphone"){h("#appForm-search-button").click()}else{if(t=="android"){h("#appForm-market-search-button").click()}}}});h("#appForm-changeIcon-link").click(function(s){s.preventDefault();h(this).hide();h("#appForm-icon-upload").show();h('#appForm input[name="img_url"]').val("")});h('input[name="app_type"]').click(function(s){h("#appForm .appForm-platformDependent").removeClass("iphone").removeClass("android").removeClass("mweb").addClass(h(this).val())}).filter(":checked").click()}function c(){l();h("#appForm.appEditForm").ajaxForm({data:{ajax:true},dataType:"json",success:function(t,u,v,s){h("#appEditForm-loading").hide();if(t.success){window.location.reload()}else{h(".form-error-text","#appForm").remove();h.each(t.errors,function(w,z){var x=z[0];var y=h("<div>").append(z[1]).addClass("form-error-text");h("input[name="+x+"]","#appForm").addClass("error").parent().append(y);h("select[name="+x+"]","#appForm").addClass("error").parent().append(y)});l();window.location.hash="";window.location.hash="appForm"}}});h("#appEditForm-submit").button({icons:{secondary:"ui-icon-circle-triangle-e"}}).click(function(s){s.preventDefault();h("#appEditForm-loading").show();h("#appForm").submit()});h("#appEditForm-cancel").click(function(s){s.preventDefault();h("#dashboard-appEditForm").slideUp("fast")});h("#dashboard-apps-editAppButton").button({icons:{primary:"ui-icon-wrench"}}).click(function(s){s.preventDefault();if(h("#dashboard-appEditForm").is(":visible")){h("#dashboard-appEditForm").slideUp("fast")}else{h("#dashboard-appEditForm").slideDown("fast")}})}function p(){h("#adunit-device_format_phone").parent().buttonset();h("#adunit-device_format_phone").click(function(s){h("#adForm-tablet-container").hide();h("#adForm-phone-container").show().find('input[type="radio"]')[0].click()});h("#adunit-device_format_tablet").click(function(s){console.log("tablet clicked");h("#adForm-phone-container").hide();h("#adForm-tablet-container").show().find('input[type="radio"]')[0].click()});h("#dashboard-apps-addAdUnitButton").button({icons:{primary:"ui-icon-circle-plus"}}).click(function(s){s.preventDefault();if(h("#dashboard-adunitAddForm").is(":visible")){h("#dashboard-adunitAddForm").slideUp("fast")}else{h("#dashboard-adunitAddForm").slideDown("fast")}});h("#adunitAddForm-submit").button({icons:{secondary:"ui-icon-circle-triangle-e"}}).click(function(s){s.preventDefault();h("#adunitForm-loading").show();h("#adunitAddForm").submit()});h("#adunitAddForm-cancel").click(function(s){s.preventDefault();h("#dashboard-adunitAddForm").slideUp("fast",function(){h("#dashboard-apps-addAdUnitButton").show()})});h("#adunitAddForm").ajaxForm({data:{ajax:true},dataType:"json",success:function(t,u,v,s){h("#adunitForm-loading").hide();if(t.success){window.location.reload()}else{l();p();window.location.hash="";window.location.hash="adunitForm"}}});h("#adForm-phone-formats").each(function(){var s=h(this);h('input[type="radio"]',s).click(function(y){var u=h(this);var x=u.parents(".adForm-format");h(".adForm-format-image").css({opacity:0.5});h(".adForm-format-image",x).css({opacity:1});var w=h(".full_only");var v=h(".banner_only");if(h(this).attr("id")=="appForm-adUnitFormat-full-tablet"||h(this).attr("id")=="appForm-adUnitFormat-full"){w.show();v.hide()}else{w.hide();v.show()}var t=h(".custom_only");if(h(this).attr("id")=="appForm-adUnitFormat-tablet-custom"||h(this).attr("id")=="appForm-adUnitFormat-custom"){t.show()}else{t.hide()}}).filter(":checked").click();h(".adForm-format-image",s).click(function(v){var u=h(this);var t=u.parents(".adForm-format");h('input[type="radio"]',t).click()});h('.adForm-format-details input[type="text"]',s).focus(function(){var t=h(this);var u=t.parents(".adForm-format");h('input[type="radio"]',u).click()})});h("#adForm-tablet-formats").each(function(){var s=h(this);h(this).find('input[type="radio"]').click(function(z){var v=h(this).parent().index();var t=h("#adForm-images-container");t.children().hide();var y=t.children()[v];h(y).show().css({opacity:1});var x=h(".full_only");var w=h(".banner_only");if(h(this).attr("id")=="appForm-adUnitFormat-full-tablet"||h(this).attr("id")=="appForm-adUnitFormat-full"){x.show();w.hide()}else{x.hide();w.show()}var u=h(".custom_only");if(h(this).attr("id")=="appForm-adUnitFormat-tablet-custom"||h(this).attr("id")=="appForm-adUnitFormat-custom"){u.show()}else{u.hide()}}).first().click()});h("#adunit-device_format_phone").parent().children().filter(":checked").click().each(function(){var t=h(this).val();var s="#adForm-"+t+"-container";h(s).find(".possible-format").click()})}function d(){p();h("#dashboard-apps-editAdUnitButton").button({icons:{primary:"ui-icon-wrench"}}).click(function(s){s.preventDefault();if(h("#dashboard-adunitEditForm").is(":visible")){h("#dashboard-adunitEditForm").slideUp("fast")}else{h("#dashboard-adunitEditForm").slideDown("fast")}});h("#adunitEditForm-submit").button({icons:{secondary:"ui-icon-circle-triangle-e"}}).click(function(s){s.preventDefault();h("#adunitForm-loading").show();h("#adunitAddForm").submit()});h("#adunitEditForm-cancel").click(function(s){s.preventDefault();h("#dashboard-adunitEditForm").slideUp("fast")});h("#adunitAddForm").ajaxForm({data:{ajax:true},dataType:"json",success:function(t,u,v,s){h("#adunitForm-loading").hide();if(t.success){window.location.reload()}else{l();p();window.location.hash="";window.location.hash="adunitForm"}}})}function n(){h(".appData-details").each(function(){var u=h(this);var v=h(".appData-details-inner",u);var t=h(".appData-details-toggleButton",u);function x(){var y=h(".ui-button-text",t);y=t;if(y.length===0){}return y}function s(){v.removeClass("hide");v.addClass("show");t.button("option",{icons:{primary:"ui-icon-triangle-1-n"}});x().text("Hide details")}function w(){v.removeClass("show");v.addClass("hide");t.button("option",{icons:{primary:"ui-icon-triangle-1-s"}});x().text("Show details")}if(v.hasClass("show")){s()}else{v.hide();w()}t.click(function(y){y.preventDefault();if(v.hasClass("show")){v.slideUp("fast");w()}else{v.slideDown("fast");s()}})})}function j(){h("#dashboard-dateOptions input").click(function(){var t=h(this).val();if(t=="custom"){h("#dashboard-dateOptions-custom-modal").dialog({width:570,buttons:[{text:"Set dates",css:{fontWeight:"600"},click:function(){var z=h("#dashboard-dateOptions-custom-from").datepicker("getDate");var v=h("#dashboard-dateOptions-custom-to").datepicker("getDate");var x=Math.ceil((v.getTime()-z.getTime())/(86400000))+1;var y=z.getDate();var u=z.getMonth()+1;var A=z.getFullYear();h(this).dialog("close");var w=document.location.href.replace(/\?.*/,"");document.location.href=w+"?r="+x+"&s="+A+"-"+u+"-"+y}},{text:"Cancel",click:function(){h(this).dialog("close")}}]})}else{var s=document.location.href.replace(/\?.*/,"");document.location.href=s+"?r="+t}});h("#stats-breakdown-dateOptions input").click(function(){h(".stats-breakdown-value").hide();h(".stats-breakdown-value."+h(this).val()).show()});h("#dashboard-dateOptions-custom-from").datepicker({defaultDate:"-15d",maxDate:"0d",onSelect:function(v){var t=h("#dashboard-dateOptions-custom-to");var s=h(this).data("datepicker");var u=h.datepicker.parseDate(s.settings.dateFormat||h.datepicker._defaults.dateFormat,v,s.settings);t.datepicker("option","minDate",u)}});h("#dashboard-dateOptions-custom-to").datepicker({defaultDate:"-1d",maxDate:"0d",onSelect:function(v){var t=h("#dashboard-dateOptions-custom-from");var s=h(this).data("datepicker");var u=h.datepicker.parseDate(s.settings.dateFormat||h.datepicker._defaults.dateFormat,v,s.settings);t.datepicker("option","maxDate",u)}})}function g(){h("#dashboard-delete-link").click(function(s){s.preventDefault();h("#dashboard-delete-modal").dialog({buttons:[{text:"Delete",click:function(){h(this).dialog("close");h("#dashboard-deleteForm").submit()}},{text:"Cancel",click:function(){h(this).dialog("close")}}]})})}function q(){h("#appForm-search-button").button({icons:{primary:"ui-icon-search"}}).click(function(v){v.preventDefault();if(h(this).button("option","disabled")){return}h("#searchAppStore-loading").show();h("#dashboard-searchAppStore-custom-modal").dialog({buttons:[{text:"Cancel",click:function(){h("#searchAppStore-results").html("");h(this).dialog("close")}}]});var t=h('#appForm input[name="name"]').val();var s=document.createElement("script");s.src="http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch?entity=software&limit=10&callback=loadedArtwork&term="+t;var u=document.getElementsByTagName("head")[0];(u||document.body).appendChild(s)})}function m(){j();h(".stats-breakdown tr").click(function(s){h("#dashboard-stats-chart").fadeOut(100,function(){mopub.Chart.setupDashboardStatsChart(a());h(this).show()})})}function o(s){}var f={initializeIndex:function(s){m();e(s.account_stats,s.start_date);i(s.app_keys);r.each(s.app_keys,function(t){k(t)});h("#dashboard-apps-addAppButton").button({icons:{primary:"ui-icon-circle-plus"}});h(".appData-id").each(function(){var u=h(this);var t=u.parents("tr");t.hover(function(){u.show()},function(){u.hide()})})},initializeGeo:function(s){m();mopub.Chart.setupDashboardStatsChart(a())},initializeAppDetail:function(s){m();c();p();g();q();n();mopub.Chart.setupDashboardStatsChart(a());h("#publisher-app-exportSelect").change(function(t){t.preventDefault();var u=h(this).val();if(u!="exp"){h("#appExportForm").find("#appExportType").val(u).end().submit()}h(this).selectmenu("index",0)});h("#publisher-app-exportSelect-menu").find("li").first().hide()},initializeAdunitDetail:function(s){m();g();n();d();mopub.Chart.setupDashboardStatsChart(a());h("#advertisers-testAdServer").button({icons:{secondary:"ui-icon-circle-triangle-e"}}).click(function(t){t.preventDefault();h("#adserverTest").dialog({buttons:{Close:function(){h(this).dialog("close")}}});h("#adserverTest-iFrame").attr("src",h("#adserverTest-iFrame-src").text())})},initializeAppCreate:function(s){m();l();p()}};window.DashboardController=f})(this.jQuery,this.Backbone,this._);var artwork_json;function loadedArtwork(c){if(!$("#dashboard-searchAppStore-custom-modal").dialog("isOpen")){return}$("#searchAppStore-results").html("");$("#searchAppStore-loading").hide();$("#dashboard-searchAppStore-custom-modal").dialog("close");artwork_json=c;var a=c.resultCount;if(a==0){$("#searchAppStore-results").append("<div class='adForm-appSearch-text' />").append("No results found");$("#dashboard-searchAppStore-custom-modal").dialog("open");return}for(var b=0;b<a;b++){if(b>10){break}var d=c.results[b];$("#searchAppStore-results").append($("<div class='adForm-appSearch' />").append($("<div class='adForm-appSearch-img' />").append($("<img />").attr("src",d.artworkUrl60).width(40).height(40)).append($("<span />"))).append($("<div class='adForm-appSearch-text' />").append($("<span />").append($('<a href="#" onclick="selectArtwork('+b+');return false";>'+d.trackName+"</a>")).append("<br />"+d.artistName))).append($("<div class='clear' />")))}$("#dashboard-searchAppStore-custom-modal").dialog("open")}function selectArtwork(a){$("#searchAppStore-results").html("");$("#appForm-icon").html("");$("#dashboard-searchAppStore-custom-modal").dialog("close");var d=artwork_json.results[a];var b=$('input:radio[name="app_type"]:checked').val();var c=$("app_form");$('#appForm input[name="name"]').val(d.trackName);$('#appForm input[name="description"]').val(d.description);if(b=="iphone"){$('#appForm input[name="url"]').val(d.trackViewUrl)}else{if(b=="android"){$('#appForm input[name="package"]').val(d.trackViewUrl)}}$('#appForm input[name="img_url"]').val(d.artworkUrl60);$('#appForm select[name="primary_category"]').val(d.primaryGenreName.toLowerCase());$('#appForm select[name="secondary_category"]').val(d.genres[1].toLowerCase());$("#appForm-icon").append($("<img />").attr("src",d.artworkUrl60).width(40).height(40).append($("<span />")))};
(function($) {

 $(document).ready(function() {


     function addPlaceholder() {
        $('.reportData-placeholder').hide();
        $('table').each(function() {
            visible = $(this).find('.reportData:visible');
            if (visible.length === 0) {
                $(this).find('.reportData-placeholder').show();
            }
        });
     }
     addPlaceholder();

    $('input[name="start"]').datepicker().change(function (e) {
        var dte = new Date($(this).val());
        $('input[name="end"]').datepicker('option', 'minDate', dte);
    });

    $('input[name="end"]').datepicker({maxDate: new Date()}).change(function (e) {
        var dte = new Date($(this).val());
        $('input[name="start"]').datepicker('option', 'maxDate', dte);
    });

    function rep_validate(form) {
        /* Check a form for selectmenu-required selectmenus
         * check for date-requireds
         * If any invalid, flag as invalid (with the pretty red colors)
         * and return False
         * if nothing invalid, return True
         */
        var success = true;
        $('#d1Error').hide();
        $('#dateError').hide();
        $('select.selectmenu-required').each(function() {
            if ($(this).val() == '') {
                $('#d1Error').show();
                success = false;
            }
        });
        $('.date-required').each(function() {
            $(this).removeClass('form-error');
            if ($(this).val() == '') {
                $(this).addClass('form-error');
                $('#dateError').show();
                success = false;
            }
        });
        return success;
    }

    var sub_label;
    if (window.location.pathname == '/reports/') {
        sub_label = 'Run';
    }
    else {
        sub_label = 'Save';
    }

    $('#reportCreateForm-submit')
    .button({
        label: sub_label,
        icons: {secondary: 'ui-icon-circle-triangle-e' }})
    .click(function(e) {
            e.preventDefault();
            if (rep_validate($('#reportCreateForm'))) {
                $('#reportCreateForm').submit();
            }
            else {
                $('#formError').show();
            }
    });

    $('#reports-view-runReportButton').button({
        icons: {secondary: 'ui-icon-circle-triangle-e' }});

    function ajaxSave() {
        $.ajax({
            url:'http://' + window.location.host + '/reports/save/' + $('#reportKey').val() + '/',
            success: function() {
                $('#reports-view-toIndex').click();
            }
        });
    }

     $('#reports-view-saveAsButton').button({icons: {secondary: 'ui-icon-check'}})
         .click(function(e) {
             e.preventDefault();
             $('#saveAs').val('True');
             $('#reportName-input').val('Copy of '+ $('#reportName-input').val());
             $('.dim-selectmenu').selectmenu('disable');
             $('#interval').selectmenu('disable');
             $('#start-input').datepicker('disable');
             $('#end-input').datepicker('disable');
             $('#reportCreateForm-submit').button({label: 'Save As'});
             $('#sched_interval').selectmenu('index', 0).change();
             $('#reportForm-container').dialog({width:750});
        });

     $('#reportCreateForm-cancel').button()
         .click(function(e) {
             e.preventDefault();
             $('#reports-reportAddForm').slideUp('fast');
         });

     $('#reports-addReportButton').button({icons: {primary: 'ui-icon-circle-plus'}})
         .click(function(e){
                e.preventDefault();
             var report_form = $('#reports-reportAddForm');
             if (report_form.is(':hidden')) {
                 $('#reports-reportAddForm').slideDown('fast');
             }
             else {
                 $('#reports-reportAddForm').slideUp('fast');
             }
         });

     $('#reports-view-editReportButton').button({icons: {primary: 'ui-icon-wrench'}})
         .click(function(e) {
             e.preventDefault();
             $('#saveAs').val('False');
             $('#reportCreateForm-submit').button({label: 'Save'});
             var report_form = $('#reportForm-container');
             report_form.dialog({width:750});
         });


     $('#reportCreateForm-cancel')
         .button()
         .click(function(e) {
             e.preventDefault();
             $('.dim-selectmenu').selectmenu('enable');
             $('#interval').selectmenu('enable');
             $('#start-input').datepicker('enable');
             $('#end-input').datepicker('enable');
             revert_state(form_state);
             $(this).parents('#reportForm-container')
                 .dialog('close');
         });

     $('#reportUpdateForm-cancel')
         .button()
         .click(function(e) {
             e.preventDefault();
             $(this).parents('#reportFormSaveAs-container')
                 .dialog('close');
         });

     $('#reportUpdateForm-submit')
         .button()
         .click(function(e) {
             e.preventDefault();
            if($('#start-input').datepicker('isDisabled')) {
                $('#start-input').datepicker('enable');
            }
            if($('#end-input').datepicker('isDisabled')) {
                $('#end-input').datepicker('enable');
            }
            $(this).parents('form').submit();
         });

     $('#reports-view-exportSelect')
         .change(function(e) {
             e.preventDefault();
             var val = $(this).val();
             if (val != 'exp') {
                 $('#reportExportForm')
                     .find('#report-exportFtype')
                     .val(val)
                     .end()
                     .submit();
             }
             $(this).selectmenu('index', 0);
        });

    $('#reports-view-exportSelect-menu').find('li').first().hide();

    $('#reports-view-exportButton')
        .click(function(e) {
            e.preventDefault();
            $('#reportExportForm').submit();
        });



    $('.int-selectmenu').selectmenu({
        style: 'popup',
        maxHeight:300,
        width:115
    });

    $('#sched_interval').selectmenu({
        style:'popup',
        maxHeight:300,
        width:135,
    });

    function fix_date(dte) {
        if (dte < 10) {
            return '0' + dte;
        }
        return dte;
    }

    function format_date(dte) {
        return fix_date(dte.getMonth() + 1) + '/' + fix_date(dte.getDate()) + '/' + dte.getFullYear();
    }


    var update = true;
    $('#interval')
        .change(function(e) {
            update = false;
            var val = $(this).val();
            var today = new Date();
            if (val != 'custom') {
                $('#interval-toggle').val(2);
                var one_day = 1000*60*60*24
                switch (val) {
                    case 'yesterday':
                        today.setTime(today.getTime() - one_day);
                        var dte = format_date(today);
                        $('#end-input').val(dte).change();
                        $('#start-input').val(dte).change();
                        break;
                    case '7days':
                        var dte = format_date(today);
                        $('#end-input').val(dte).change();
                        today.setTime(today.getTime() - (7*one_day));
                        dte = format_date(today);
                        $('#start-input').val(dte).change();
                        break;
                    case 'lmonth':
                        var this_mo = today.getMonth();
                        while (today.getMonth() == this_mo) {
                            today.setTime(today.getTime() - one_day);
                        }
                        var dte = format_date(today);
                        $('#end-input').val(dte).change();
                        today.setDate(1);
                        dte = format_date(today);
                        $('#start-input').val(dte).change();
                        break;
                }
            }
            else {
                return;
            }
        }).change();

    $('.date-field')
        .change(function(e) {
            var inter_val = $('#interval-toggle').val()
            if ($('#interval-toggle').val() == 0) {
                $('#interval').selectmenu('index', 3);
            }
            else {
                $('#interval-toggle').val(inter_val - 1);
            }
        });

    var selects = $('.dim-selectmenu').selectmenu({
        style: 'popup',
        maxHeight:320,
        width:110
    });

    d1_sel = $(selects[0]);
    d2_sel = $(selects[1]);
    d3_sel = $(selects[2]);

    function revert_state(state) {
        d1_sel.selectmenu('index', state.d1);
        d1_validate($('#d1'));
        d2_sel.selectmenu('index', state.d2);
        d2_validate($('#d2'));
        d3_sel.selectmenu('index', state.d3);
        $('#end-input').val(state.end);
        $('#start-input').val(state.start);
        $('#interval').selectmenu('index', state.interv);
        $('#sched_interval').selectmenu('index', state.sched_interv);
        // Trigger those on change events what whatttt
        $('#interval').change();
        $('#sched_interval').change();
        $("#reportName-input").val(state.name);
        if (state.email) {
            $('#email-input-checkbox').attr('checked');
        }
        else {
            $('#email-input-checkbox').removeAttr('checked');
        }
    }

    function get_form_state() {
        return build_state( sel_state(d1_sel),
                            sel_state(d2_sel),
                            sel_state(d3_sel),
                            sel_state($('#interval')),
                            sel_state($('#sched_interval')),
                            $('#end-input').val(),
                            $('#start-input').val(),
                            $('#reportName-input').val(),
                            $('#email-input-checkbox')
                          );
    }
    function build_state(d1, d2, d3, interv, sched_interv, end, start, name, email) {
        return {
            d1: d1,
            d2: d2,
            d3: d3,
            interv: interv,
            sched_interv: sched_interv,
            end: end,
            start: start,
            name: name,
            email:email.is(':checked'),
        };
    }
    function sel_state(obj) {
        return obj.selectmenu('index');
    }
    //Get the state of the form so we go back to this on cancel
    var form_state = get_form_state();


    $('#d1').change(
        function(e) {
            if ($(this).val() != '') {
                $('#d1Error').hide();
            }
            e.preventDefault();
            d1_validate($(this));
            d2_validate($('#d2'));
        }).change();


    function d1_validate(obj) {
            var idx = obj.selectmenu('index');
            //start with everything enabled
            for (var i = 0; i < 14; i++) {
                d3_sel.selectmenu('enable', i);
                d2_sel.selectmenu('enable', i);
            }
            var d2_idx = d2_sel.selectmenu("index");
            var d3_idx = d3_sel.selectmenu("index");
            $('#d2-show').show();
            switch(obj.val()) {
                case '':
                    d2_sel.selectmenu("index", 0);
                    d3_sel.selectmenu("index", 0);
                    $('#d2-show').hide();
                    $('#d3-show').hide();
                    break;
                case 'adunit':
                    if (d2_idx == 2) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 2) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '2');
                    d3_sel.selectmenu('disable', '2');

                case 'app':
                    if (d2_idx == 1) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 1) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '1');
                    d3_sel.selectmenu('disable', '1');
                    break;

                case 'creative':
                    if (d2_idx == 5) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 5) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '5');
                    d3_sel.selectmenu('disable', '5');

                case 'campaign':
                    if (d2_idx == 4) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 4) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '4');
                    d3_sel.selectmenu('disable', '4');

                case 'priority':
                    if (d2_idx == 3) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 3) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '3');
                    d3_sel.selectmenu('disable', '3');
                    break;
                case 'hour':
                    if (d2_idx == 9) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 9) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '9');
                    d3_sel.selectmenu('disable', '9');
                case 'day':
                    if (d2_idx == 8) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 8) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '8');
                    d3_sel.selectmenu('disable', '8');
                case 'week':
                    if (d2_idx == 7) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 7) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '7');
                    d3_sel.selectmenu('disable', '7');
                case 'month':
                    if (d2_idx == 6) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 6) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '6');
                    d3_sel.selectmenu('disable', '6');
                    break;
                case 'country':
                    if (d2_idx == 10) {
                        d2_sel.selectmenu("index", 0);
                    }
                    if (d3_idx == 10) {
                        d3_sel.selectmenu("index", 0);
                    }
                    d2_sel.selectmenu('disable', '10');
                    d3_sel.selectmenu('disable', '10');
                    break;
                case 'marketing':
                    if (d2_idx == 11) {
                        d2_sel.selectmenu('index', 0);
                    }
                    if (d3_idx == 11) {
                        d3_sel.selectmenu('index', 0);
                    }
                    d2_sel.selectmenu('disable', 11);
                    d3_sel.selectmenu('disable', 11);
                    break;
                case 'os_ver':
                    if (d2_idx == 13) {
                        d2_sel.selectmenu('index', 0);
                    }
                    if (d3_idx == 13) {
                        d3_sel.selectmenu('index', 0);
                    }
                    d2_sel.selectmenu('disable', 13);
                    d3_sel.selectmenu('disable', 13);
                case 'os':
                    if (d2_idx == 12) {
                        d2_sel.selectmenu('index', 0);
                    }
                    if (d3_idx == 12) {
                        d3_sel.selectmenu('index', 0);
                    }
                    d2_sel.selectmenu('disable', 12);
                    d3_sel.selectmenu('disable', 12);
                    break;
                default:
                    break;
            }
    }

    $('#d2').change(
        function(e) {
            e.preventDefault();
            d1_validate($('#d1'));
            d2_validate($(this));
        });

    $('.update-button').change(
        function(e) {
            e.preventDefault();
            if (!obj_equals(form_state, get_form_state())) {
                $('#reportCreateForm-submit').button({label:'Save and Run'});
            }
            else {
                $('#reportCreateForm-submit').button({label:'Save'});
            }
        }).change();



function obj_equals(x, y) {
    for(p in y) {
        if(typeof(x[p])=='undefined') {return false;}
    }
    for(p in y) {
        if (y[p]) {
            switch(typeof(y[p])) {
              case 'object':
                if (!y[p].equals(x[p])) { return false }; break;
              case 'function':
                if (typeof(x[p])=='undefined' || (p != 'equals' && y[p].toString() != x[p].toString())) { return false; }; break;
            default:
                if (y[p] != x[p]) { return false; }
            }
        }
        else {
            if (x[p]) {
                return false;
            }
        }
    }
    for(p in x){
        if(typeof(y[p])=='undefined') {return false;}
    }
    return true;
}




     function d2_validate(obj) {
         var idx = obj.selectmenu('index');
        //start with everything enabled
        var d3_idx = d3_sel.selectmenu("index");
        $('#d3-show').show();
        switch(obj.val()) {
            case '':
                d3_sel.selectmenu("index", 0);
                $('#d3-show').hide();
                break;
            case 'adunit':
                if (d3_idx == 2) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '2');
            case 'app':
                if (d3_idx == 1) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '1');
                break;

            case 'creative':
                if (d3_idx == 5) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '5');
            case 'campaign':
                if (d3_idx == 4) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '4');
            case 'priority':
                if (d3_idx == 3) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '3');
                break;

            case 'hour':
                if (d3_idx == 9) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '9');
            case 'day':
                if (d3_idx == 8) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '8');
            case 'week':
                if (d3_idx == 7) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '7');
            case 'month':
                if (d3_idx == 6) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '6');
                break;
            case 'country':
                if (d3_idx == 10) {
                    d3_sel.selectmenu("index", 0);
                }
                d3_sel.selectmenu('disable', '10');
                break;
            case 'marketing':
                if (d3_idx == 11) {
                    d3_sel.selectmenu('index', 0);
                }
                d3_sel.selectmenu('disable', 11);
                break;
            case 'os_ver':
                if (d3_idx == 13) {
                    d3_sel.selectmenu('index', 0);
                }
                d3_sel.selectmenu('disable', 13);
            case 'os':
                if (d3_idx == 12) {
                    d3_sel.selectmenu('index', 0);
                }
                d3_sel.selectmenu('disable', 12);
                break;
            default:
                break;
        }
    }


    $("#sched_interval")
    .change(function(e) {
        $('.schedule-help').hide();
        $('.schedule-help.'+$(this).val()).show();
    }).change();

    $("#email-input-checkbox")
    .change(function(e) {
        if ($(this).attr('checked')) {
            $('#email-recipients').show();
        } else {
            $('#email-recipients').hide();
        }
    }).change();

    $('#reportStateChangeForm-delete')
        .click(function(e) {
            e.preventDefault();
            $('#reportStateChangeForm').find('#action').val('delete').end().submit();
        });

 });
})(this.jQuery);

