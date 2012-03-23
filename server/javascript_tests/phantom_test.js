/*
 * I'm not sure what this is going to be yet, but phantom is pretty awesome
 and we should use it.
 */ 

/*
 * Utility
 */

function simulateClick() {
    var evt = document.createEvent("MouseEvents");
    evt.initMouseEvent("click", true, true, window,
                       0, 0, 0, 0, 0, false, false, 
                       false, false, 0, null);
    var cb = document.getElementById("checkbox"); 
    var canceled = !cb.dispatchEvent(evt);
    if(canceled) {
        // A handler called preventDefault
        alert("canceled");
    } else {
        // None of the handlers called preventDefault
        alert("not canceled");
    }
}

var host = "http://localhost:8000";
var urls = [
    "/inventory/",
];

/*
 * Tests the number of requests a page load will make.
 */

if (phantom.args.length == 0) {
    console.log('Pass some args brah');
    phantom.exit();
} else {
    phantom.args.forEach(function (arg, i) {
        console.log(i + ": " + arg);
    });
}

var page = new WebPage();

page.onResourceRequested = function (request) {
    console.log('Request ' + JSON.stringify(request, undefined, 4));
};

page.onResourceReceived = function (response) {
    console.log('Receive ' + JSON.stringify(response, undefined, 4));
};

page.open(host + urls[0]);

// quickstart
// http://code.google.com/p/phantomjs/wiki/QuickStart

// integration with jasmine: 
// http://code.google.com/p/phantomjs/wiki/TestFrameworkIntegration