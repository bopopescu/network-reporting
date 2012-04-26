from copy import copy

class NetworkScrapeRecord(object):
    def __init__(self, revenue=0, attempts=0, impressions=0, clicks=0,
            app_tag=None):
        self.revenue = revenue
        self.attempts = attempts
        self.impressions = impressions
        self.clicks = clicks
        # app_tag is always the pub_id
        self.app_tag = app_tag

    # For debugging
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        properties = copy(self.__dict__)
        properties['app_tag'] = properties['app_tag'].encode('utf8')
        return '<NetworkScrapeRecord app_tag:%(app_tag)s revenue:%(revenue)s ' \
                'attempts:%(attempts)d impressions:%(impressions)d clicks' \
                ':%(clicks)d>' % properties

