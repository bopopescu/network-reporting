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
