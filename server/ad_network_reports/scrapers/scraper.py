class ScraperSite(object):
    def __init__(self, id, name, url, description):
        self.identifier = id
        self.name = name
        self.url = url
        self.description = description

class NetworkConfidential(object):
    pass

class Scraper(object):
    """Default Scraper abstract object.

    All scrapers implement this class and it's methods. They're all weird as
    fuck with roughly 0 things in common though...
    """

    # This needs to be set for all scrapers
    NETWORK_NAME = None

    def __init__(self, credentials):
        """Credentials has a 'network' field, in the subclasses
        double check to make sure they are correct.  For sanity.
        """
        if credentials.ad_network_name != self.NETWORK_NAME:
            raise RuntimeError("Invalid credentials.  Attempting to use %s" \
                    "credentials for an %s scraper" % (credentials.network,
                        self.NETWORK_NAME))
        self.username = credentials.username
        self.password = credentials.password
        self.key = str(credentials.key())

    def get_site_stats(self, start_date):
        """Start_date is a datetime objects."""
        raise NotImplementedError("Subclasses of Scraper must implement this "
                "method.")

