var adunitData = [
    {
        active: true,
        attempts: 1000,
        clicks: 103,
        ctr: 103/1000,
        ecpm: 0,
        fill_rate: 0,
        impressions: 1000,
        name: 'Really great adunit',
        price_floor: 0.25,
        revenue: 4002.02
    },
    {
        active: false,
        attempts: 2,
        clicks: 1,
        ctr: .5,
        ecpm: 0,
        fill_rate: 0,
        impressions: 0,
        name: 'Really horrible adunit',
        price_floor: 0,
        revenue: .34
    }
];

describe("AdUnit", function () {

    beforeEach(function() {
        this.adunit = new AdUnit(adunitData[0]);
        this.altadunit = new AdUnit(adunitData[1]);
    });

    it("is created from data", function () {
        expect(this.adunit.get('price_floor')).toEqual(0.25);
    });

    it("can be active or not", function () {
        expect(this.adunit.get('active')).toBeTruthy();
        expect(this.altadunit.get('active')).toBeFalsy();
    });
});


var appData = [
    {
        name: 'Robot Unicorn Attack',
        url:'#',
        revenue: 1000,
        attempts: 12309,
        icon_url: "/placeholders/image.gif",
        impressions: 23409,
        fill_rate: 12309,
        clicks: 2432,
        price_floor: 0.25,
        app_type: 'iOS',
        ecpm: 324,
        ctr: 312
    },
    {
        name: 'Robot Unicorn Attack Metal Edition',
        url:'#',
        revenue: 10002,
        attempts: 123039,
        icon_url: "/placeholders/image.gif",
        impressions: 231409,
        fill_rate: 123039,
        clicks: 24321,
        price_floor: 0.95,
        app_type: 'iOS',
        ecpm: 3234,
        ctr: 3122
    }
];

describe("App", function () {

    beforeEach(function() {
        this.app = new App(appData[0]);
        this.altapp = new App(appData[1]);
    });

    it("is created from data", function () {
        expect(this.app.get('price_floor')).toEqual(0.25);
        expect(this.altapp.get('price_floor')).toEqual(0.95);
    });
});


