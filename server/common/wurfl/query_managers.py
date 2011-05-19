from common.wurfl.wurfl_dicts import (BRAND_MAR,
                                     BRAND_OS,
                                     BRAND_OSVER,
                                     MAR_OS,
                                     MAR_OSVER,
                                     OS_BRAND,
                                     OS_MAR,
                                     OS_OSVER,
                                     OSVER_BRAND,
                                     OSVER_MAR,
                                     )

class WurflQueryManager():

    #need to get brand name attached to marketing name
    @classmethod
    def reports_get_marketing(cls, os, os_ver, brand):
        brand_mars = None
        os_mars = None
        if brand is not None:
            brand_mars = BRAND_MAR[brand]
        if os and os_ver is None:
            os_mars = OS_MAR[os]
        elif (os and os_ver) or (os_ver and os is None):
            os_mars = OSVER_MAR[os_ver]
        #brand, os, and os_ver are all None, return all marketing names (fuuucckkkk)
        else:
            return reduce(lambda x, y: x+y, BRAND_MAR.values())
        #return only those names in both the os set and the brand set
        if os_mars and brand_mars:
            ret = []
            for mar in os_mars:
                if mar in brand_mars:
                    ret.append(mar)
            return ret
        #brand_mars is none, return only the os stuff
        elif os_mars:
            return os_mars
        #os_mars is none, return only brand stuff
        else:
            return brand_mars


    @classmethod
    def reports_get_brand(cls, os, os_ver):
        #if os_ver is not none use it, regardless of what os is
        if os_ver:
            return OSVER_BRAND[os_ver]
        elif os:
            return OS_BRAND[os]
        #both are none, return all
        else:
            return reduce(lambda x,y: x+y, OS_BRAND.values())

    @classmethod
    def reports_get_os(cls, brand, market):
        if market:
            return MAR_OS[market]
        elif brand:
            return BRAND_OS[brand]
        else:
            return reduce(lambda x,y: x+y, BRAND_OS.values())

    @classmethod
    def reports_get_osver(cls, brand, market, os):
        os_mars = None
        brand_mars = None
        if os is not None:
            os_mars = OS_OSVER[os]
        if brand and market is None:
            brand_mars = BRAND_OSVER[brand]
        elif (brand and market) or (market and brand is None):
            brand_mars = MAR_OSVER[market]
        #brand, os, and os_ver are all None, return all marketing names (fuuucckkkk)
        else:
            return reduce(lambda x, y: x+y, brand_mars.values())
        #return only those names in both the os set and the brand set
        if os_mars and brand_mars:
            ret = []
            for mar in os_mars:
                if mar in brand_mars:
                    ret.append(mar)
            return ret
        #brand_mars is none, return only the os stuff
        elif os_mars:
            return os_mars
        #os_mars is none, return only brand stuff
        else:
            return brand_mars





