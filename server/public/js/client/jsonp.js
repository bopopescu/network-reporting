function callback(data) {
    var iframe = document.getElementById('mopub-iframe');
    iframe = (iframe.contentWindow)  ? iframe.contentWindow : (iframe.contentDocument.document);
    iframe.document.open();
    iframe.document.write(data.ad);
    iframe.document.close();
    mopub_click_url = data.click_url;
}

//do jsonp call
fake_data = { ad: '<b> BEST HTML DATA EVER </b>', click_url: 'http://localhost:8000/CHECKITOUTHISURLISGETTINGPINGTHISISAWESOMEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'};
callback(fake_data);
