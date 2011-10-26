﻿$(function() {
   $("#loginCredentials").submit(function(event) {
	   event.preventDefault();
	   // Check if data submited is valid.
	   $.ajax({url: 'http://checklogincredentials.mopub.com:8888',
		   data: $(this).serialize(),
		   crossDomain: true, 
		   dataType: "jsonp",
	           success: function(valid) {
	           	   // Upon success update the database
			   if (valid) {
				if (account_key) {
					$.post("/ad_network_reports/manage/" + account_key + "/add/",
						$("#loginCredentials").serialize(), function() {
							window.location = "/ad_network_reports/manage/" + account_key;
						});
				} else {
					$.post("/ad_network_reports/add/",
						$("#loginCredentials").serialize(), function() {
							window.location = "/campaigns/";
						});
				}
			   } else {
				$("#error").html("Invalid login information.")
			   }
		   }
	   });
    });
})
