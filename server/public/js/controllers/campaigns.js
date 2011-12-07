$(function() {
	CampaignsController = function(gtee_adgroups_data, promo_adgroups_data, backfill_promo_adgroups_data, ajax_query_string) {
		// Guaranteed
		var gtee_adgroups = new AdGroups(gtee_adgroups_data);
		var gtee_adgroups_view = new AdGroupsView({
			collection: gtee_adgroups,
			el: '#gtee-adgroups',
			title: 'Guaranteed Campaigns',
			type: 'gtee'
		});
		gtee_adgroups_view.render();
		gtee_adgroups.each(function(adgroup) { adgroup.fetch({ data: ajax_query_string }); });

		// Promotional
		var promo_adgroups = new AdGroups(promo_adgroups_data);
		var promo_adgroups_view = new AdGroupsView({
			collection: promo_adgroups,
			el: '#promo-adgroups',
			title: 'Promotional Campaigns',
			type: 'promo'
		});
		promo_adgroups_view.render();
		promo_adgroups.each(function(adgroup) { adgroup.fetch({ data: ajax_query_string }); });

		// Backfill Promotional
		var backfill_promo_adgroups = new AdGroups(backfill_promo_adgroups_data);
		var backfill_promo_adgroups_view = new AdGroupsView({
			collection: backfill_promo_adgroups,
			el: '#backfill-promo-adgroups',
			title: 'Backfill Promotional Campagins',
			type: 'backfill_promo'
		});
		backfill_promo_adgroups_view.render();
		backfill_promo_adgroups.each(function(adgroup) { adgroup.fetch({ data: ajax_query_string }); });
	};
});