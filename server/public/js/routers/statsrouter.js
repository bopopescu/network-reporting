(function($, Backbone, _) {

    var StatsRouter = Backbone.Router.extend({
        // could include a 'vs' parameter for showing deltas
        routes : {
            "/daily/start/:start_date/end/:end_date": "fetchStatsForDays",
            "/hourly/start/:start_date/end/:end_date": "fetchStatsForHours",
            "/weekly/start/:start_date/end/:end_date": "fetchStatsForWeeks",
        },
        fetchStatsForDays: function(start_date, end_date) {
            var granularity = 'daily';
        },
        fetchStatsForHours: function(start_date, end_date) {
            var granularity = 'hourly';

        },
        fetchStatsForWeeks: function(start_date, end_date) {
            var granularity = 'weekly';
        }

    });


})(window.jQuery, window.Backbone, window._);
