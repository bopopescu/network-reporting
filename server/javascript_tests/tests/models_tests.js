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

    it("should parse the 'android' app_type correctly as 'Android'", function () {

        this.server.respondWith(
            "GET",
            "/api/app/2?&endpoint=all",
            [
                200,
                {"Content-Type": "text/plain"},
                '{"id": 2,"app_type": "android"}'
            ]
        );

        var app = new App({id: 2});

        var onError = app.fetch();

        onError.error(function(a, b, c){
            console.log(a);
            console.log(b);
            console.log(c);
        });

        this.server.respond();

        expect(app.attributes).toContainAttrs({
            id: 2,
            app_type: "Android"
        });
    });


    // it("should parse the 'iphone' app_type correctly as 'iOS'", function () {

    //     this.server.respondWith("GET", "/api/app/1",
    //                             [200, {"Content-Type": "application/json"},
    //                              "{'id': 1, 'app_type': 'iphone'}"]);

    //     var app = new App({id: 1});
    //     app.fetch();
    //     this.server.respond();

    //     expect(app.attributes).toContainAttrs({
    //         id: 1,
    //         app_type: "iOS"
    //     });

    // });

    // it("should parse the 'mweb' app_type correctly as 'Mobile Web'", function () {

    //     this.server.respondWith("GET", "/api/app/3",
    //                             [200, {"Content-Type": "application/json"},
    //                              "{'id': 3, 'app_type': 'mweb'}"]);

    //     var app = new App({id: 3});
    //     app.fetch();
    //     this.server.respond();

    //     expect(app.attributes).toContainAttrs({
    //         id: 3,
    //         app_type: "Mobile Web"
    //     });
    // });

});


describe("App Collection", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();
    });

});


describe("AdUnit Model", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();
    });

});


describe("AdUnit Collection", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();
    });

});



describe("AdGroup Model", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();
    });

});

describe("AdGroups Collection", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();
    });

});


describe("Campaign Model", function() {
    beforeEach(function() {
        this.server = sinon.fakeServer.create();
    });

});


describe("Model Helpers", function() {

    it("should correctly calculate ctr", function () {

    });

    it("should correctly calculate fill_rate", function () {

    });

    it("should correctly format click_count", function () {

    });

    it("should correctly format conversion_count", function () {

    });

    it("should correctly format goal", function () {

    });

    it("should correctly format impression_count", function () {

    });

    it("should correctly format request_count", function () {

    });

    it("should correctly format cpm", function () {

    });

    it("should correctly format revenue", function () {

    });

    it("should correctly format conv_rate", function () {

    });

    it("should correctly format ctr", function () {

    });

    it("should correctly format fill_rate", function () {

    });

    it("should correctly format status", function () {

    });

    it("should throw errors for stats that aren't supported", function () {

    });


});