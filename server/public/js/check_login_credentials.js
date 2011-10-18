$(function() {
   $("#loginCredentials").submit(function() {
	   // Check if data submited is valid.
	   $.ajax({
		   url: 'http://checklogincredentials.mopub.com:8888',
	   	   type: "POST",
	           data: $(this).serialize(),
	           // Upon success update the database
	           success: function() {
			   $.post("/ad_network_reports/add/",
		           	$(this).serialize())
		   }
	           error: function() {
				  $("#error").html("Invalid login information.")
		   }
	   })
    });
})
