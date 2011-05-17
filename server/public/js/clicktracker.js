var adSenseDeliveryDone;
var adSensePx;
var adSensePy;

function adSenseGetMouse(evt)
{
    var e;
    if (evt.touches) {
        e = evt.touches[0];
    }
    else {
        e = evt;
    }
    // Adapted from http://www.howtocreate.co.uk/tutorials/javascript/eventinfo
    if (typeof e.pageX  == 'number')
    {
        //most browsers
        adSensePx = e.pageX;
        adSensePy = e.pageY;
    }
    else if (typeof e.clientX  == 'number')
    {
        //Internet Explorer and older browsers
        //other browsers provide this, but follow the pageX/Y branch
        adSensePx = e.clientX;
        adSensePy = e.clientY;

        if (document.body && (document.body.scrollLeft || document.body.scrollTop))
        {
            //IE 4, 5 & 6 (in non-standards compliant mode)
            adSensePx += document.body.scrollLeft;
            adSensePy += document.body.scrollTop;
        }
        else if (document.documentElement && (document.documentElement.scrollLeft || document.documentElement.scrollTop ))
        {
            //IE 6 (in standards compliant mode)
            adSensePx += document.documentElement.scrollLeft;
            adSensePy += document.documentElement.scrollTop;
        }
    }
}

function adSenseFindX(obj)
{
    var x = 0;
    while (obj)
    {
        x += obj.offsetLeft;
        obj = obj.offsetParent;
    }
    return x;
}

function adSenseFindY(obj)
{
    var y = 0;
    while (obj)
    {
        y += obj.offsetTop;
        obj = obj.offsetParent;
    }

    return y;
}

function adSensePageExit(e)
{
    if (typeof adSensePx == 'undefined') {
        return;
    }

    var ad = document.getElementById("mopub-iframe");
    var adLeft = adSenseFindX(ad);
    var adTop = adSenseFindY(ad);
    var adRight = parseInt(adLeft) + parseInt(ad.width) + 15;
    var adBottom = parseInt(adTop) + parseInt(ad.height) + 10;
    console.log('left: ' + adLeft + ' top: ' + adTop + ' right: ' + adRight + ' bottom: ' + adBottom);
    var inFrameX = (adSensePx > (adLeft - 10) && adSensePx < adRight);
    var inFrameY = (adSensePy > (adTop - 10) && adSensePy < adBottom);



    if (inFrameY && inFrameX)
    {
        var i = new Image();
        i.src = mopub_click_url;
    }
}

function adSenseInit()
{
    if (typeof window.addEventListener != 'undefined')
    {
        // other browsers
        document.body.onunload=adSensePageExit;
        document.body.ontouchend=adSensePageExit;
        //document.body.addEventListener('unload', adSensePageExit, false);
        window.addEventListener('mousemove', adSenseGetMouse, false);
        window.addEventListener('touchstart', adSenseGetMouse, false);
        window.addEventListener('touchmove', adSenseGetMouse, false);
    }
}

function adSenseDelivery()
{
    if (typeof adSenseDeliveryDone != 'undefined' && adSenseDeliveryDone)
        return;

    adSenseDeliveryDone = true;

    if(typeof window.addEventListener != 'undefined')
    {
        //.. gecko, safari, konqueror and standard
        window.addEventListener('load', adSenseInit, false);
    }
    else
    {
        //.. mac/ie5 and anything else that gets this far
        //if there's an existing onload function
        if(typeof window.onload == 'function')
        {
            //store it
            var existing = onload;

            //add new onload handler
            window.onload = function()
            {
                //call existing onload function
                existing();

                //call adsense_init onload function
                adSenseInit();
            };
        }
        else
        {
            //setup onload function
            window.onload = adSenseInit;
        }
    }
}

//adSenseDelivery();
