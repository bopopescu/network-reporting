class NetworkScrapeRecord:
    def __init__(self, attempts, impressions, clicks, ecpm, fill_rate=0, ctr=0, app_name=None):
        self.attempts = attempts
        self.impressions = impressions
        self.fill_rate = fill_rate
        self.clicks = clicks
        self.ctr = ctr
        self.ecpm = ecpm
        self.app_name = app_name
        