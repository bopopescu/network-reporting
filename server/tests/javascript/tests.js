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


describe("number formatting helpers", function () {

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


    it("format_kmbt works correctly for different orders of magnitude", function () {

        var t = function(value, with_decimal, expected) {
            var actual = DashboardHelpers.format_kmbt(value, with_decimal);
            expect(actual).toEqual(expected);
        };

        t(1.0, false, "1");
        t(10.0, false, "10");
        t(100.0, false, "100");
        t(1000.0, false, "1K");
        t(10000.0, false, "10K");
        t(100000.0, false, "100K");
        t(1000000.0, false, "1M");
        t(10000000.0, false, "10M");
        t(100000000.0, false, "100M");
        t(1000000000.0, false, "1B");
        t(10000000000.0, false, "10B");
        t(100000000000.0, false, "100B");
        t(1000000000000.0, false, "1T");
        t(10000000000000.0, false, "10T");
        t(100000000000000.0, false, "100T");
        
    });

    it("format_kmbt works with decimal numbers if specified", function () {

        var t = function(value, with_decimal, expected) {
            var actual = DashboardHelpers.format_kmbt(value, with_decimal);
            expect(actual).toEqual(expected);
        };

        t(1.0, true, "1.00");
        t(10.0, true, "10.00");
        t(100.0, true, "100.00");
        t(1000.0, true, "1.00K");
        t(10000.0, true, "10.00K");
        t(100000.0, true, "100.00K");
        t(1000000.0, true, "1.00M");
        t(10000000.0, true, "10.00M");
        t(100000000.0, true, "100.00M");
        t(1000000000.0, true, "1.00B");
        t(10000000000.0, true, "10.00B");
        t(100000000000.0, true, "100.00B");
        t(1000000000000.0, true, "1.00T");
        t(10000000000000.0, true, "10.00T");
        t(100000000000000.0, true, "100.00T");

        t(2.25, true, "2.25");
        t(45.98, true, "45.98");
        t(339.12, true, "339.12");
        t(1992.45, true, "1.99K");
        t(86275.09, true, "86.27K");
        t(782012, true, "782.01K");
        t(9873190.6, true, "9.87M");
        t(77930284.50, true, "77.93M");
        t(192840285, true, "192.84M");
        t(4895928374.80, true, "4.89B");
        t(62956028467.19, true, "62.95B");
        t(123895239874.83, true, "123.89B");
        t(8829332100394.47, true, "8.82T");
        t(33003011749013.51, true, "33.00T");
        t(999820156757293.77, true, "999.82T");

    });

    it('format_stat formats the different stat properties correctly', function () {

        var t = function(stat, value, expected) {
            var actual = DashboardHelpers.format_stat(stat, value);
            expect(actual).toEqual(expected);
        };


        t('rev', 10.0, '$10.00');
        t('rev', 1000.0, '$1.00K');
        t('rev', 1323231.0, '$1.32M');
        
    });

    it('calculate_stats calculates derivative values (conv_rate, cpm, ctr, fill_rate) in place', function () {});

    it('pad adds a zero to the front of an integer if its less than 10', function () {});

});


describe("date formatting helpers", function () {
    
    it('string_to_date converts a string to a date', function () {
        
        var t = function(string, expected) {
            var actual = DashboardHelpers.string_to_date(string);
            expect(actual).toEqual(expected);
        };

        t('2012-01-01', new Date(2012, 0, 1));
        t('2012-1-1', new Date(2012, 0, 1));
        t('2012-2-29', new Date(2012, 1, 29));
        t('2012-02-25', new Date(2012, 1, 25));
        t('1012-9-7', new Date(1012, 8, 7));
        t('2012-03-11', new Date(2012, 2, 11));
        t('2012-03-11', new Date(2012, 2, 11));
        t('2012-03-11', new Date(2012, 2, 11));
        t('2012-03-11', new Date(2012, 2, 11));
        t('2012-3-11', new Date(2012, 2, 11));

    });

    it('date_to_string converts a date to a string', function () {});
    it('pretty_string_to_date converts a pretty string to a date', function () {});
    it('date_to_pretty_string converts a date to a pretty string', function () {});
    it('date_hour_to_string converts a datehour to a string', function () {});
    it('string_to_date_hour converts a string to a datehour', function () {});

});


describe("charts", function () {

    

});


describe("queries", function () {

    // function get_query_response(query) {
    //     return 'Got it!';
    // }

    // beforeEach(function() {

    //     registerFakeAjax({
    //         "/test_url": function () {
    //             console.log(arguments);
    //             return get_query_response;
    //         }
    //     });

    //     $.jsonp.setup({
    //         callbackParameter: "callback",
    //         url: "/test_url",
    //     });


    // });

    // it('makes jsonp calls', function(){
    //     $.jsonp({

    //         data: {
    //             'hello': 'goodbye'
    //         },
            
    //     });
    // });

});


describe('page rendering', function () {
    
    

});