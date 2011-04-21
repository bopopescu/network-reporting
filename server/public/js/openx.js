/**
 *
 * +---------------------------------------------------------------------------+
 * | OpenX v${RELEASE_MAJOR_MINOR}                                                                |
 * | ======${RELEASE_MAJOR_MINOR_DOUBLE_UNDERLINE}                                                                 |
 * |                                                                           |
 * | Copyright (c) 2003-2009 OpenX Limited                                     |
 * | For contact details, see: http://www.openx.org/                           |
 * |                                                                           |
 * | This program is free software; you can redistribute it and/or modify      |
 * | it under the terms of the GNU General Public License as published by      |
 * | the Free Software Foundation; either version 2 of the License, or         |
 * | (at your option) any later version.                                       |
 * |                                                                           |
 * | This program is distributed in the hope that it will be useful,           |
 * | but WITHOUT ANY WARRANTY; without even the implied warranty of            |
 * | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             |
 * | GNU General Public License for more details.                              |
 * |                                                                           |
 * | You should have received a copy of the GNU General Public License         |
 * | along with this program; if not, write to the Free Software               |
 * | Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA |
 * +---------------------------------------------------------------------------+
 * $Id$
 *
 * The compressed version of this file is used in the delivery engine
 * If you make changes to this file, recompress it:
 *  - http://dean.edwards.name/packer/
 * and update the copy in /lib/max/Delivery/templates/adg.js
 */
var phpAds_adSenseDeliveryDone;
var phpAds_adSensePx;
var phpAds_adSensePy;

function phpAds_adSenseGetMouse(e)
{
    // Adapted from http://www.howtocreate.co.uk/tutorials/javascript/eventinfo
    if (typeof e.pageX  == 'number')
    {
        //most browsers
        phpAds_adSensePx = e.pageX;
        phpAds_adSensePy = e.pageY;
    }
    else if (typeof e.clientX  == 'number')
    {
        //Internet Explorer and older browsers
        //other browsers provide this, but follow the pageX/Y branch
        phpAds_adSensePx = e.clientX;
        phpAds_adSensePy = e.clientY;

        if (document.body && (document.body.scrollLeft || document.body.scrollTop))
        {
            //IE 4, 5 & 6 (in non-standards compliant mode)
            phpAds_adSensePx += document.body.scrollLeft;
            phpAds_adSensePy += document.body.scrollTop;
        }
        else if (document.documentElement && (document.documentElement.scrollLeft || document.documentElement.scrollTop ))
        {
            //IE 6 (in standards compliant mode)
            phpAds_adSensePx += document.documentElement.scrollLeft;
            phpAds_adSensePy += document.documentElement.scrollTop;
        }
    }
}

function phpAds_adSenseFindX(obj)
{
    var x = 0;
    while (obj)
    {
        x += obj.offsetLeft;
        obj = obj.offsetParent;
    }
    return x;
}

function phpAds_adSenseFindY(obj)
{
    var y = 0;
    while (obj)
    {
        y += obj.offsetTop;
        obj = obj.offsetParent;
    }

    return y;
}

function phpAds_adSensePageExit(e)
{
    var ad = document.getElementById("mopub-iframe");
    if (typeof phpAds_adSensePx == 'undefined') {
        return;
    }

    var adLeft = phpAds_adSenseFindX(ad);
    var adTop = phpAds_adSenseFindY(ad);
    var adRight = parseInt(adLeft) + parseInt(ad.width) + 15;
    var adBottom = parseInt(adTop) + parseInt(ad.height) + 10;
    var inFrameX = (phpAds_adSensePx > (adLeft - 10) && phpAds_adSensePx < adRight);
    var inFrameY = (phpAds_adSensePy > (adTop - 10) && phpAds_adSensePy < adBottom);

    if (inFrameY && inFrameX)
    {
        var i = new Image();
        i.src = mopub_click_url;
    }
}

function phpAds_adSenseInit()
{
    if (typeof window.addEventListener != 'undefined')
    {
        // other browsers
        document.body.onunload=phpAds_adSensePageExit;
        //document.body.addEventListener('unload', phpAds_adSensePageExit, false);
        window.addEventListener('mousemove', phpAds_adSenseGetMouse, true);
    }
}

function phpAds_adSenseDelivery()
{
    if (typeof phpAds_adSenseDeliveryDone != 'undefined' && phpAds_adSenseDeliveryDone)
        return;

    phpAds_adSenseDeliveryDone = true;

    if(typeof window.addEventListener != 'undefined')
    {
        //.. gecko, safari, konqueror and standard
        window.addEventListener('load', phpAds_adSenseInit, false);
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
                phpAds_adSenseInit();
            };
        }
        else
        {
            //setup onload function
            window.onload = phpAds_adSenseInit;
        }
    }
}

phpAds_adSenseDelivery();
