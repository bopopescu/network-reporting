/*
 * # Tests for models.js
 */

/*
 * ## Tests for App Model
 */
describe("App Model", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();

        this.addMatchers({
            toContainAttrs: function(expected) {
                for (attribute in expected) {
                    var actual = this.actual;
                    if (!actual.hasOwnProperty(attribute)) {
                        return false;
                    }
                    if (actual[attribute] !== expected[attribute]) {
                        return false;
                    }
                }
                return true;
            }
        });
    });

    afterEach(function() {
        this.server.restore();
    });

    it("should parse the 'mweb' app_type correctly as 'Mobile Web'", function () {

        this.server.respondWith(
            "GET",
            "/api/app/1?&endpoint=all",
            [
                200,
                {"Content-Type": "application/json"},
                '[{"id": 1,"app_type": "mweb"}]'
            ]
        );

        var app = new App({id: 1});

        app.fetch();

        this.server.respond();

        expect(app.attributes).toContainAttrs({
            id: 1,
            app_type: "Mobile Web"
        });
    });



    it("should parse the 'android' app_type correctly as 'Android'", function () {

        this.server.respondWith(
            "GET",
            "/api/app/2?&endpoint=all",
            [
                200,
                {"Content-Type": "application/json"},
                '[{"id": 2,"app_type": "android"}]'
            ]
        );

        var app = new App({id: 2});
        app.fetch();

        this.server.respond();

        expect(app.attributes).toContainAttrs({
            id: 2,
            app_type: "Android"
        });
    });


    it("should parse the 'iphone' app_type correctly as 'iOS'", function () {

        this.server.respondWith(
            "GET",
            "/api/app/3?&endpoint=all",
            [
                200,
                {"Content-Type": "application/json"},
                '[{"id": 3,"app_type": "iphone"}]'
            ]
        );

        var app = new App({id: 3});
        app.fetch();
        this.server.respond();

        expect(app.attributes).toContainAttrs({
            id: 3,
            app_type: "iOS"
        });
    });



});

/*
 * # AdUnit Tests
 */
describe("AdUnit Model", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();

        this.addMatchers({
            toContainAttrs: function(expected) {
                for (attribute in expected) {
                    var actual = this.actual;
                    if (!actual.hasOwnProperty(attribute)) {
                        return false;
                    }
                    if (actual[attribute] !== expected[attribute]) {
                        return false;
                    }
                }
                return true;
            }
        });
    });

    afterEach(function() {
        this.server.restore();
    });

    it("should only validate if the price floor is a number", function(){
        var adunit = new AdUnit();
        var status = adunit.set({
            price_floor: 0.5
        });

        expect(status).toBeTruthy();

        status = adunit.set({
            price_floor: "0.5"
        });

        expect(status).toBeTruthy();

        status = adunit.set({
            price_floor: "0.5a"
        });

        expect(status).toEqual(false);
    });
});



/*
 * # AppCollection tests
 */
describe("App Collection", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();

        this.addMatchers({
            toContainAttrs: function(expected) {
                for (attribute in expected) {
                    var actual = this.actual;
                    if (!actual.hasOwnProperty(attribute)) {
                        return false;
                    }
                    if (actual[attribute] !== expected[attribute]) {
                        return false;
                    }
                }
                return true;
            }
        });
    });

    afterEach(function() {
        this.server.restore();
    });

    it("should fetch collections for each of its adunits", function () {

        function makeAdUnit(appid) {
            return '{"id": ' + appid +',"app_type": "mweb"}';
        }

        this.server.respondWith(
            "GET",
            "/api/app/?&endpoint=all",
            [
                200,
                {"Content-Type": "application/json"},
                '[{"id": 1,"app_type": "mweb"}, {"id": 2,"app_type": "android"}, {"id": 3,"app_type": "iphone"}]'
            ]
        );

        var callback = sinon.spy();
        var apps = new AppCollection();
        apps.bind('update', callback);
        apps.fetch();
        this.server.respond();

        this.server.respondWith(
            "GET", /\/api\/app\/(\d+)\/adunits\/?&endpoint=all/,
            function (xhr, id) {
                xhr.respond(200,
                            {"Content-Type": "application/json"},
                            '[' + makeAdUnit(id) + ']');
            }
        );

        apps.fetchAdUnits();
        this.server.respond();

        expect(apps.adunits.length).toEqual(3);
    });

});


describe("AdUnit Collection", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();

        this.addMatchers({
            toContainAttrs: function(expected) {
                for (attribute in expected) {
                    var actual = this.actual;
                    if (!actual.hasOwnProperty(attribute)) {
                        return false;
                    }
                    if (actual[attribute] !== expected[attribute]) {
                        return false;
                    }
                }
                return true;
            }
        });
    });

    afterEach(function() {
        this.server.restore();
    });
});



describe("AdGroup Model", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();

        this.addMatchers({
            toContainAttrs: function(expected) {
                for (attribute in expected) {
                    var actual = this.actual;
                    if (!actual.hasOwnProperty(attribute)) {
                        return false;
                    }
                    if (actual[attribute] !== expected[attribute]) {
                        return false;
                    }
                }
                return true;
            }
        });
    });

    afterEach(function() {
        this.server.restore();
    });

});

describe("AdGroups Collection", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();

        this.addMatchers({
            toContainAttrs: function(expected) {
                for (attribute in expected) {
                    var actual = this.actual;
                    if (!actual.hasOwnProperty(attribute)) {
                        return false;
                    }
                    if (actual[attribute] !== expected[attribute]) {
                        return false;
                    }
                }
                return true;
            }
        });
    });

    afterEach(function() {
        this.server.restore();
    });

});


describe("Campaign Model", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();

        this.addMatchers({
            toContainAttrs: function(expected) {
                for (attribute in expected) {
                    var actual = this.actual;
                    if (!actual.hasOwnProperty(attribute)) {
                        return false;
                    }
                    if (actual[attribute] !== expected[attribute]) {
                        return false;
                    }
                }
                return true;
            }
        });
    });

    afterEach(function() {
        this.server.restore();
    });

});


describe("Model Helpers", function() {

    it("should correctly calculate ctr", function () {
        var result1 = ModelHelpers.calculate_ctr(1000, 10);
        expect(result1).toEqual(0.01);

        var result2 = ModelHelpers.calculate_ctr(0, 10);
        expect(result2).toEqual(0);

        var result3 = ModelHelpers.calculate_ctr(null, 10);
        expect(result3).toEqual(null);

        var result4 = ModelHelpers.calculate_ctr(0, null);
        expect(result4).toEqual(null);
    });

    it("should correctly calculate fill_rate", function () {
        var result1 = ModelHelpers.calculate_fill_rate(10000, 1000);
        expect(result1).toEqual(0.1);

        var result2 = ModelHelpers.calculate_fill_rate(0, 10);
        expect(result2).toEqual(0);

        var result3 = ModelHelpers.calculate_fill_rate(null, 10);
        expect(result3).toEqual(null);

        var result4 = ModelHelpers.calculate_fill_rate(0, null);
        expect(result4).toEqual(null);
    });

    it("should correctly format click_count", function () {
        var result1 = ModelHelpers.format_stat('click_count', 1000);
        expect(result1).toEqual("1,000");

        var result2 = ModelHelpers.format_stat('click_count', 1000000);
        expect(result2).toEqual("1,000,000");
    });

    it("should correctly format conversion_count", function () {
        var result1 = ModelHelpers.format_stat('conversion_count', 1000);
        expect(result1).toEqual("1,000");

        var result2 = ModelHelpers.format_stat('conversion_count', 1000000);
        expect(result2).toEqual("1,000,000");
    });

    it("should correctly format goal", function () {
        var result1 = ModelHelpers.format_stat('goal', 1000);
        expect(result1).toEqual("1,000");

        var result2 = ModelHelpers.format_stat('goal', 1000000);
        expect(result2).toEqual("1,000,000");
    });

    it("should correctly format impression_count", function () {
        var result1 = ModelHelpers.format_stat('impression_count', 1000);
        expect(result1).toEqual("1,000");

        var result2 = ModelHelpers.format_stat('impression_count', 1000000);
        expect(result2).toEqual("1,000,000");
    });

    it("should correctly format request_count", function () {
        var result1 = ModelHelpers.format_stat('request_count', 1000);
        expect(result1).toEqual("1,000");

        var result2 = ModelHelpers.format_stat('request_count', 1000000);
        expect(result2).toEqual("1,000,000");
    });

    it("should correctly format cpm", function () {
        var small_result = ModelHelpers.format_stat('cpm', 0.001);
        expect(small_result).toEqual('$0.00');

        var smallish_result = ModelHelpers.format_stat('cpm', 0.01);
        expect(smallish_result).toEqual('$0.01');

        var rounds_down = ModelHelpers.format_stat('cpm', 0.995);
        expect(rounds_down).toEqual('$0.99');

        var rounds_up = ModelHelpers.format_stat('cpm', 0.996);
        expect(rounds_up).toEqual('$1.00');

        var no_decimal = ModelHelpers.format_stat('cpm', 1);
        expect(no_decimal).toEqual('$1.00');

        var large_result = ModelHelpers.format_stat('cpm', 1234567.89);
        expect(large_result).toEqual('$1,234,567.89');

    });

    it("should correctly format revenue", function () {
        var small_result = ModelHelpers.format_stat('revenue', 0.001);
        expect(small_result).toEqual('$0.00');

        var smallish_result = ModelHelpers.format_stat('revenue', 0.01);
        expect(smallish_result).toEqual('$0.01');

        var rounds_down = ModelHelpers.format_stat('revenue', 0.995);
        expect(rounds_down).toEqual('$0.99');

        var rounds_up = ModelHelpers.format_stat('revenue', 0.996);
        expect(rounds_up).toEqual('$1.00');

        var no_decimal = ModelHelpers.format_stat('revenue', 1);
        expect(no_decimal).toEqual('$1.00');

        var large_result = ModelHelpers.format_stat('revenue', 1234567.89);
        expect(large_result).toEqual('$1,234,567.89');
    });

    it("should correctly format conv_rate", function () {
        var result = ModelHelpers.format_stat('conv_rate', 0.10);
        expect(result).toEqual('10.00%');

        var result2 = ModelHelpers.format_stat('conv_rate', 10);
        expect(result2).toEqual('1000.00%');
    });

    it("should correctly format ctr", function () {
        var result = ModelHelpers.format_stat('ctr', 0.10);
        expect(result).toEqual('10.00%');

        var result2 = ModelHelpers.format_stat('ctr', 10);
        expect(result2).toEqual('1000.00%');
    });

    it("should correctly format fill_rate", function () {
        var result = ModelHelpers.format_stat('fill_rate', 0.10);
        expect(result).toEqual('10.00%');

        var result2 = ModelHelpers.format_stat('fill_rate', 10);
        expect(result2).toEqual('1000.00%');
    });

    it("should correctly format status", function () {
        var result = ModelHelpers.format_stat('status','foo');
        expect(result).toEqual('foo');
    });

    it("should correctly format null values", function () {
        var result = ModelHelpers.format_stat('goal', null);
        expect(result).toEqual('--');
    });

    it("should throw errors for stats that aren't supported", function () {
        try {
            var result = ModelHelpers.format_stat('UNSUPPORTED', 'foo');
        } catch (x) {
            expect(x).toEqual('Unsupported stat "UNSUPPORTED".');
        }

    });

});