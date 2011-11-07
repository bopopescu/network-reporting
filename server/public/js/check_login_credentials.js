$(function() {
   $("#loginCredentials").submit(function(event) {
	   event.preventDefault();
	   // Check if data submited is valid.
	   data = $(this).serialize();
	   data += ("&account_key=" + account_key);
	   $.ajax({url: 'http://checklogincredentials.mopub.com',
		   data: data,
		   crossDomain: true, 
		   dataType: "jsonp",
	     success: function(valid) {
		     // Upon success update the database
		     if (valid) {
			     if (management_mode) {
				     window.location = "/ad_network_reports/manage/" + account_key;
			     } else {
				     window.location = "/ad_network_reports/";
			     }
		     } else {
			     $("#error").html("Invalid login information.")
		     }
	     }
	   });
    });
})
