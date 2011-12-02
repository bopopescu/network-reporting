$(function() {
	CampaignsController = function(gtee_adgroups_data, promo_adgroups_data, backfill_promo_adgroups_data) {
		// Guaranteed
		var gtee_adgroups = new AdGroups();
		var gtee_adgroups_rollup_view = new AdGroupsRollupView({
			collection: gtee_adgroups,
			el: '#gtee-rollups tbody'
		})
		var gtee_adgroups_table_view = new GteeAdGroupsTableView({
			collection: gtee_adgroups,
			el: '#gteeCampaignDataTables'
		});
		gtee_adgroups.reset(gtee_adgroups_data);

		// Promotional
		var promo_adgroups = new AdGroups();
		var promo_adgroups_rollup_view = new AdGroupsRollupView({
			collection: promo_adgroups,
			el: '#promo-rollups tbody'
		})
		var promo_adgroups_table_view = new AdGroupsTableView({
			collection: promo_adgroups,
			el: '#campaignDataTable-promo tbody'
		});
		promo_adgroups.reset(promo_adgroups_data);

		// Backfill Promotional
		var backfill_promo_adgroups = new AdGroups();
		var backfill_promo_adgroups_rollup_view = new AdGroupsRollupView({
			collection: backfill_promo_adgroups,
			el: '#backfill-promo-rollups tbody'
		})
		var backfill_promo_adgroups_table_view = new AdGroupsTableView({
			collection: backfill_promo_adgroups,
			el: '#campaignDataTable-backfill-promo tbody'
		});
		backfill_promo_adgroups.reset(backfill_promo_adgroups_data);
	};
});