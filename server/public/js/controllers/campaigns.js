$(function() {
	CampaignsController = function(gtee_adgroups_data, promo_adgroups_data, backfill_promo_adgroups_data) {
		// Guaranteed
		var gtee_adgroups = new AdGroups();
		var gtee_adgroups_view = new AdGroupsView({
			collection: adgroups,
			el: '#gtee-adgroups',
			title: 'Guaranteed Campaigns',
			type: 'gtee'
		});
		gtee_adgroups.reset(gtee_adgroups_data);

		// Promotional
		var promo_adgroups = new AdGroups();
		var promo_adgroups_view = new AdGroupsView({
			collection: adgroups,
			el: '#promo-adgroups',
			title: 'Promotional Campaigns',
			type: 'promo'
		});
		promo_adgroups.reset(promo_adgroups_data);

		// Backfill Promotional
		var backfill_promo_adgroups = new AdGroups();
		var backfill_promo_adgroups_view = new AdGroupsView({
			collection: adgroups,
			el: '#backfill-promo-adgroups',
			title: 'Backfill Promotional Campagins',
			type: 'backfill_promo'
		});
		backfill_promo_adgroups.reset(backfill_promo_adgroups_data);
	};
});