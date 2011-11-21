from google.appengine.ext import db

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from account.models import Account
from publisher.models import App

class AdNetworkLoginCredentials(db.Model): #(account,ad_network_name)
    account = db.ReferenceProperty(Account, required = True,
            collection_name='login_credentials')
    ad_network_name = db.StringProperty(required=True)

    # Needed for all networks but mobfox
    username = db.ByteStringProperty()

    # Needed to store the username securely
    username_iv = db.ByteStringProperty()

    password = db.ByteStringProperty()

    # Needed to store the password securely
    password_iv = db.ByteStringProperty()

    # Needed for admob
    client_key = db.StringProperty()

    email = db.BooleanProperty(default = False)

    is_active = db.BooleanProperty(default=True)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s:%s' % (kwargs['account'].key(), kwargs['ad_network_name']))
        super(AdNetworkLoginCredentials, self).__init__(*args, **kwargs)


    @classmethod
    def get_by_ad_network_name(cls, account, ad_network_name):
        return cls.get_by_key_name('k:%s:%s' % (account.key(), ad_network_name))

class AdNetworkAppMapper(db.Model): #(ad_network_name,publisher_id)
    ad_network_name = db.StringProperty(required=True)
    publisher_id = db.StringProperty(required=True)

    ad_network_login = db.ReferenceProperty(AdNetworkLoginCredentials,
                                            collection_name='ad_network_app_mappers')
    application = db.ReferenceProperty(App, collection_name='ad_network_app_mappers')

    # If a network contains information for an app that the publisher
    # hasn't entered into mopub, mark this false
    app_in_mopub = db.BooleanProperty(default=True)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s:%s' % (kwargs['ad_network_name'],
                                               kwargs['publisher_id']))
        super(AdNetworkAppMapper, self).__init__(*args, **kwargs)

    @classmethod
    def get_by_publisher_id(cls, publisher_id, ad_network_name):
        return cls.get_by_key_name('k:%s:%s' % (ad_network_name, publisher_id))




    def has_potential_errors(self):
        """
        If the mapper doesn't have scrape stats, there may have been an error
        collecting stats from that network. This method will return a boolean
        True if stats exist and false if they don't, so that we can tell from
        within the template if an error might have occured.
        """

        stats = AdNetworkScrapeStats.all().filter('ad_network_app_mapper =', self).get()

        return stats == None

class AdNetworkScrapeStats(db.Model): #(AdNetworkAppMapper, date)
    ad_network_app_mapper = db.ReferenceProperty(AdNetworkAppMapper,
                                                 required=True,
                                                 collection_name='ad_network_stats')
    date = db.DateProperty(required=True)

    # stats info for a specific day
    revenue = db.FloatProperty()
    attempts = db.IntegerProperty()
    impressions = db.IntegerProperty()
    fill_rate = db.FloatProperty()
    clicks = db.IntegerProperty()
    ctr = db.FloatProperty()
    ecpm = db.FloatProperty()

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s:%s' % (kwargs[
                    'ad_network_app_mapper'].key(), kwargs['date'].
                    strftime('%Y-%m-%d')))
        super(AdNetworkScrapeStats, self).__init__(*args, **kwargs)

    @classmethod
    def get_by_app_mapper_and_day(cls, app_mapper, day):
        return cls.get_by_key_name('k:%s:%s' % (app_mapper.key(),
            day.strftime('%Y-%m-%d')))

    @classmethod
    def get_by_app_mapper_and_days(cls, app_mapper_key, days):
        return [stats for stats in cls.get_by_key_name(['k:%s:%s' % (
            app_mapper_key, day.strftime('%Y-%m-%d')) for day in days]) if stats
            != None]

class AdNetworkManagementStats(db.Model): #(date)
    date = db.DateProperty(required=True)

    # Could be done with the Expando class but probably better to make
    # explicit.

    admob_found = db.IntegerProperty(default=0)
    admob_updated = db.IntegerProperty(default=0)
    admob_mapped = db.IntegerProperty(default=0)
    admob_login_failed = db.IntegerProperty(default=0)

    jumptap_found = db.IntegerProperty(default=0)
    jumptap_updated = db.IntegerProperty(default=0)
    jumptap_mapped = db.IntegerProperty(default=0)
    jumptap_login_failed = db.IntegerProperty(default=0)

    iad_found = db.IntegerProperty(default=0)
    iad_updated = db.IntegerProperty(default=0)
    iad_mapped = db.IntegerProperty(default=0)
    iad_login_failed = db.IntegerProperty(default=0)

    inmobi_found = db.IntegerProperty(default=0)
    inmobi_updated = db.IntegerProperty(default=0)
    inmobi_mapped = db.IntegerProperty(default=0)
    inmobi_login_failed = db.IntegerProperty(default=0)

    mobfox_found = db.IntegerProperty(default=0)
    mobfox_updated = db.IntegerProperty(default=0)
    mobfox_mapped = db.IntegerProperty(default=0)
    mobfox_login_failed = db.IntegerProperty(default=0)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s' % kwargs['date'].
                    strftime('%Y-%m-%d'))
        super(AdNetworkManagementStats, self).__init__(*args, **kwargs)

    def increment(self, field):
        setattr(self, field, getattr(self, field) + 1)

    @classmethod
    def get_by_day(cls, day):
        return cls.get_by_key_name('k:%s' % day.strftime('%Y-%m-%d'))

    @classmethod
    def get_by_days(cls, days):
        return [stats for stats in cls.get_by_key_name(['k:%s' % day.strftime(
            '%Y-%m-%d') for day in days]) if stats != None]
