class NetworkScrapeRecord(object):
    def __init__(self, revenue, attempts, impressions, clicks, ecpm=0.0,
            fill_rate=0.0, ctr=0.0, app_tag=None):
        self.revenue = revenue
        self.attempts = attempts
        self.impressions = impressions
        self.fill_rate = fill_rate
        self.clicks = clicks
        self.ctr = ctr
        self.ecpm = ecpm
        self.app_tag = app_tag

    # For debugging    
    def __str__(self):
        self.__repr__()

    def __repr__(self):
        return ('<NetworkScrapeRecord app_tag:%(app_tag)s revenue:%(revenue)s '
                'attempts:%(attempts)d impressions:%(impressions)d fill_rate:'
                '%(fill_rate).2f clicks:%(clicks)d ctr:%(ctr).2f ecpm:%(ecpm)'
                '.2f>' % self.__dict__)

