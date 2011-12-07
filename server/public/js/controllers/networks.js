$(function() {
	// TODO: document
	/*
	 *   adgroups_data
	 *   graph_start_date
	 *   today
	 *   yesterday
	 *   ajax_query_string
	 */
	NetworksController = function(adgroups_data, graph_start_date, today, yesterday, ajax_query_string) {
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

		adgroups.each(function(adgroup) { adgroup.fetch({ data: ajax_query_string }); });

		// TODO: put this random stuff in the correct place

        $("#add_campaign_button").button({ icons : { primary : 'ui-icon-circle-plus'} });

		$.each(['pause', 'resume', 'activate', 'archive', 'delete'], function(iter, action) {
			$('#campaignForm-' + action)
			.click(function(e) {
				e.preventDefault();
				$('#campaignForm').find("#action").attr("value", action).end().submit();
			});
		});

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
	};
});