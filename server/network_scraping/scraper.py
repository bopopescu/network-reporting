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
    
    def __init__(self, credentials):
        ''' Credentials has a 'network' field, in the subclasses
        double check to make sure they are correct.  For sanity '''
        # self.account = credentials.account
        self.username = credentials['username']
        self.password = credentials['password']

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




        
    
