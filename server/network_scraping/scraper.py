import re

import cookielib
import mechanize


class MyCookieJar(cookielib.LWPCookieJar):

    def _cookie_from_cookie_tuple(self, tup, request):
        name, value, standard, rest = tup
        version = standard.get('version', None)
        if version is not None:
            standard['version'] = version.strip('"')
        return cookielib.LWPCookieJar._cookie_from_cookie_tuple(self, tup, request)


class ScraperSite(object):
    def __init__(self, id, name, url, description):
        self.id = id
        self.name = name
        self.url = url
        self.description = description

ScraperAdunit = ScraperSite

class ScraperAd(object):
    pass

ScraperCreative = ScraperAd

class ScraperAdGroup(object):
    pass

class ScraperCampaign(object):
    pass

class Scraper(object):
    ''' Default Scraper objects, all scrapers should implement
    this class and it's methods.  They're all going to be weird as fuck
    with roughly 0 in common though...'''
    
    # This needs to be set for all scrapers
    NETWORK_NAME = None
    
    def __init__(self, credentials):
        ''' Credentials has a 'network' field, in the subclasses
        double check to make sure they are correct.  Also automatically
        autheticates the scraper since they're all gonna do that anyway.'''
        if credentials.network != self.NETWORK_NAME:
            raise "Invalid credentials.  Attempting to use %s credentials for an %s scraper" % (credentials.network, self.NETWORK_NAME)
        self.account = credentials.account
        self.username = credentials.username
        self.password = credentials.password

        # Initialize the mechanize stuff
        self.browser = mechanize.Browser()

        cj = MyCookieJar()
        self.browser.set_cookiejar(cj)

        # Browser opts
        self.browser.set_handle_equiv(True)
        self.browser.set_handle_gzip(True)
        self.browser.set_handle_redirect(True)
        self.browser.set_handle_referer(True)
        self.browser.set_handle_robots(False)

        self.browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    
        # Engage super cheats
        self.browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

        self.authenticate()

    def authenticate(self, **kwargs):
        ''' This function should do two things: if we need cookies and stuff to mess
        with various pages it should acquire those (useful for real scraping, not API stuff).
        It should also get the required keys, tokens, etc to do stuff with the APIs.

        Example: Admob needs a unique token every time you access the API, this function 
        should get and set that token for that instance of the scraper.

        It is conceivable that we'll eventually want to literally scrape adnetworks pages for 
        pub ids and things in which case we need to use the login info to actually log in and
        get the required cookies so we can access pages at will with this object '''
        raise "Not implemented yet"

    def get_site_stats(self, start_date, end_date, ids=None, **kwargs):
        ''' Start_date and end_date are datetime objects '''
        raise "Not implemented yet"

    def get_adunit_stats(self, start_date, end_date, ids=None, **kwargs):
        ''' For sanity ''' 
        return self.get_site_stats(start_date, end_date, ids, **kwargs)

    def get_pub_ids(self, **kwargs):
        ''' Going to be unique for each ad network, but this is for filling out the forms.  This 
        shouldn't be implemented for a while.  But when it is it will be siickkk '''
        raise "Not implemented yet"

    def get_sites(self):
        ''' Returns a list of ScraperSite objects.  For AdMob this is a simple API query, for everyone 
        else we'll probably have to do the cookie shit '''
        raise "Not implemented yet"

    def get_adunits(self):
        ''' For sanity '''
        return self.get_sites()


    ############## AdMob Specific ################
    def get_ad_stats(self, start_date, end_date, ids=None, **kwargs):
        raise "Not implemented yet" 

    def get_ad_group_stats(self, start_date, end_date, ids=None, **kwargs):
        raise "Not implemented yet"

    def get_campaign_stats(self, start_date, end_date, ids=None, **kwargs):
        raise "Not implemented yet"
    
    ############## 1337 Scrape Stuff #############
    # *Disclaimer*: Nick logic follows           #
    #                                            #
    # AdMob is basically trying to do what we're #
    # doing, the idea here is that eventually    #
    # people can just put in their AdMob creds   #
    # and we can auto-generate their campaigns,  #
    # creatives, adgroups, and sites without the #
    # user having to really do anything.  Also   #
    # the stats for these are exposed in their   #
    # API                                        #
    ##############################################
    def get_ads(self):
        ''' Returns a list of ScraperAd objects.  Used to build actual
        Creative DB objects for this account'''
        raise "Not implemented yet"

    def get_ad_groups(self):
        ''' Returns a list of ScraperAdGroup objects.  Used to build actual 
        AdGroup DB objects for this account'''
        raise "Not implemented yet"

    def get_campaigns(self):
        ''' Returns a list of ScraperCampaign objects. Used to build actual
        Campaign DB objects for this account'''
        raise "Not implemented yet"
    ############### END AdMob Specific ############




        
    
