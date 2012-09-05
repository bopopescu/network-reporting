(function($) {
  return $.fn.ajaxChosen = function(settings, callback) {
    var chosenXhr, defaultOptions, options, select;
    if (settings == null) {
      settings = {};
    }
    if (callback == null) {
      callback = function() {};
    }
    defaultOptions = {
      minTermLength: 3,
      afterTypeDelay: 500,
      jsonTermKey: "term"
    };
    select = this;
    chosenXhr = null;
    options = $.extend({}, defaultOptions, settings);
    this.chosen();
    return this.each(function() {
      return $(this).next('.chzn-container').find(".search-field > input, .chzn-search > input").bind('keyup', function() {
        var field, msg, success, val;
        val = $.trim($(this).attr('value'));
        msg = val.length < options.minTermLength ? "Keep typing..." : "Looking for '" + val + "'";
        select.next('.chzn-container').find('.no-results').text(msg);
        if (val === $(this).data('prevVal')) {
          return false;
        }
        $(this).data('prevVal', val);
        if (this.timer) {
          clearTimeout(this.timer);
        }
        if (val.length < options.minTermLength) {
          return false;
        }
        field = $(this);
        if (!(options.data != null)) {
          options.data = {};
        }
        options.data[options.jsonTermKey] = val;
        if (options.dataCallback != null) {
          options.data = options.dataCallback(options.data);
        }
        success = options.success;
        options.success = function(data) {
          var items, selected_values;
          if (!(data != null)) {
            return;
          }
          selected_values = [];
          select.find('option').each(function() {
            if (!$(this).is(":selected")) {
              return $(this).remove();
            } else {
              return selected_values.push($(this).val() + "-" + $(this).text());
            }
          });
          items = callback(data);
          $.each(items, function(value, text) {
            if ($.inArray(value + "-" + text, selected_values) === -1) {
              return $("<option />").attr('value', value).html(text).appendTo(select);
            }
          });
          if (success != null) {
            success(data);
          }
          var rem = field.attr('value');
          select.trigger("liszt:updated");
          field.attr('value', rem);
          var $first_active = field.closest('.chzn-container').find('.active-result').first();
          $first_active.mouseover();
          // select.result_do_highlight($first_active);
          return field.css('width', 'auto');
        };
        return this.timer = setTimeout(function() {
          if (chosenXhr) {
            chosenXhr.abort();
          }
          return chosenXhr = $.ajax(options);
        }, options.afterTypeDelay);
      });
    });
  };
})(jQuery);
