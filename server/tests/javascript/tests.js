/*
 * Utility functions
 */

// Checks to see if a datapoint has all of the necessary 
// properties set
function validate_datapoint(datapoint) {
    
}

function validate_series(series) {
    
}

function validate_query(query) {
    
}


describe("helpers", function () {
    it("get_data_from_datapoint parses dates correctly", function () {

        var t = function (seed_key, seed_value, expected) {
            var datapoint = {
                req: 275,
                rev: 100.0,
                imp: 250,
                clk: 40,
                attempts: 0,
                conv: 5,
            };
            datapoint[seed_key] = seed_value;

            var actual = DashboardHelpers.get_date_from_datapoint(datapoint);
            expect(actual).toEqual(expected);
        };


        t("date", "2012-01-01-00", "1/1");
        t("date", "2012-02-29-12", "2/29");
        t("date", "2012-03-20-19", "3/20");
        t("date", "2012-04-20-08", "4/20");
        t("date", "2012-05-01-23", "5/1");
        t("date", "2012-06-01-00", "6/1");
        t("date", "2012-07-01-10", "7/1");

        t("hour", "2012-01-01-00", "1/1 00:00");
        t("hour", "2012-02-29-12", "2/29 12:00");
        t("hour", "2012-03-20-19", "3/20 19:00");
        t("hour", "2012-04-20-08", "4/20 08:00");
        t("hour", "2012-05-01-23", "5/1 23:00");
        t("hour", "2012-06-01-00", "6/1 00:00");
        t("hour", "2012-07-01-10", "7/1 10:00");

        t("sentinel", "2012-01-01-00", null);
        t("sentinel", "2012-02-29-12", null);
        t("sentinel", "2012-03-20-19", null);
        t("sentinel", "2012-04-20-08", null);
        t("sentinel", "2012-05-01-23", null);
        t("sentinel", "2012-06-01-00", null);
        t("sentinel", "2012-07-01-10", null);
    });


    it("format_stat works correctly for different types", function () {
        
        var t = function(stat, value, expected) {
            var actual = DashboardHelpers.format_stat(stat, value);
            expect(actual).toEqual(expected);
        };

        t("rev", 1.0, "$1");
        t("rev", 10.0, "$10");
        t("rev", 100.0, "$100");
        t("rev", 1000.0, "$1,000");
        t("rev", 10000.0, "$10K");
        t("rev", 100000.0, "$100K");
        t("rev", 10000000.0, "$1,000K");
        t("rev", 100000000.0, "$10M");
        t("rev", 1000000000.0, "$100M");
        t("rev", 10000000000.0, "$1,000M");
        t("rev", 100000000000.0, "$10B");
        t("rev", 1000000000000.0, "$100B");
        t("rev", 10000000000000.0, "$1,000B");
        t("rev", 100000000000000.0, "$10T");
        t("rev", 1000000000000000.0, "$100T");
        t("rev", 10000000000000000.0, "$1,000T");

        
    });

    it("format_kmbt works correctly for different orders of magnitude", function () {
        
    });

});


describe("charts", function () {

});


describe("queries", function () {
    it("get_data_from_datapoint", function () {

    });
});


