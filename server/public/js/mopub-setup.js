/*
  MoPub Setup Pages JS
*/

// global mopub object
var mopub = mopub || {};

(function($){
  // dom ready
  $(document).ready(function() {
    
    // Submit button
    $('#appForm-submit')
      .button({ 
        icons: { secondary: "ui-icon-circle-triangle-e" } 
      })
      .click(function(e) {
        e.preventDefault();
        $('#appForm').submit();
    });
    
    // Search button
    $('#appForm-search-button')
      .button({ icons: { primary: "ui-icon-search" }, disabled: true})
      .click(function(e) {
        e.preventDefault();
        if ($(this).button( "option", "disabled" ))
          return;

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
                       + 'entity=software&limit=10&callback=loadedArtwork&term='+name;
        var head = document.getElementsByTagName("head")[0];
        (head || document.body).appendChild( script );
    });
    
    /*---------------------------------------/
    / App Details Form
    /---------------------------------------*/
    
    // Platform-dependent URL/package name switching
    $('#appForm input[name="app_type"]').click(function(e) {
      $('#appForm .appForm-platformDependent')
        .removeClass('iphone')
        .removeClass('android')
        .addClass($(this).val());
    }).filter(':checked').click(); // make sure we're in sync when the page loads

    // Populate ad unit name based on app name
    $('input[name="name"]').change(function() {
      var name = $.trim($(this).val());
      $('#appForm-adUnitName').val(name + ' banner ad');
    });
    
    // Toggle enabled/disabled state of search button when app name changes
    $('#appForm-name').keyup(function(e) {
      // Show/hide the app search button
      var name = $.trim($(this).val());
      if (name.length)
        $('#appForm-search-button').button("enable");
      else
        $('#appForm-search-button').button("disable");
      if (e.keyCode == 13) {
        $('#appForm-search-button').click();
      }
    }).keyup();
    
    // Change icon
    $('#appForm-changeIcon-link').click(function (e) {
      e.preventDefault();
      $(this).hide();
      $('#appForm-icon-upload').show();
      $('#appForm input[name="img_url"]').val('');
    });
    
    /*---------------------------------------/
    / Ad Unit Form
    /---------------------------------------*/
    
    // Set up format selection UI
    $('.adForm-formats').each(function() {
      var container = $(this);
      $('input[type="radio"]', container).click(function(e) {
        var radio = $(this);
        var formatContainer = radio.parents('.adForm-format');

        $('.adForm-format-image', container).css({ opacity: 0.5 });
        $('.adForm-format-image', formatContainer).css({ opacity: 1 });

        if(radio.val() == 'custom') {
          // $('.adForm-format-details input[type="text"]:first', formatContainer).focus();
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
  });
})(this.jQuery);

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
  }
  else {
    for (var i=0;i<resultCount;i++) {
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
      )
    }
  }
  
  $('#dashboard-searchAppStore-custom-modal').dialog("open");
}

function selectArtwork(index) {
  $('#searchAppStore-results').html('');
  $('#appForm-icon').html('');
  $('#dashboard-searchAppStore-custom-modal').dialog("close");

  var app = artwork_json['results'][index];

  var form = $('app_form');
  $('#appForm input[name="name"]').val(app['trackName'])
  $('#appForm input[name="description"]').val(app['description'])
  $('#appForm input[name="url"]').val(app['trackViewUrl'])
  $('#appForm input[name="img_url"]').val(app['artworkUrl60'])
  
  $('#appForm-icon').append($("<img />")
    .attr("src",app['artworkUrl60'])
    .width(40)
    .height(40)
    .append($("<span />"))
  )
}