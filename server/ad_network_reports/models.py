import logging
from google.appengine.ext import db

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from account.models import Account
from publisher.models import App

KEY = 'V("9L^4z!*QCF\%"7-/j&W}BZmDd7o.<'

class AdNetworkLoginCredentials(db.Model): #(account,ad_network_name)
    account = db.ReferenceProperty(Account, required=True,
            collection_name='login_credentials')
    ad_network_name = db.StringProperty(required=True)

    # Needed for all networks but mobfox
    _username = db.ByteStringProperty()

    # Needed to store the username securely
    username_iv = db.ByteStringProperty()

    _password = db.ByteStringProperty()

    # Needed to store the password securely
    password_iv = db.ByteStringProperty()

    # Needed for admob
    client_key = db.StringProperty()

    email = db.BooleanProperty(default=False)

    # List of application publisher ids that aren't tracked in MoPub.
    app_pub_ids = db.StringListProperty(default=[])

    def __init__(self, *args, **kwargs):
        self.password = kwargs['password']
        self.username = kwargs['username']
        kwargs['password'] = self.password
        kwargs['username'] = self.username
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s:%s' % (kwargs['account'].key(),
                kwargs['ad_network_name']))
        super(AdNetworkLoginCredentials, self).__init__(*args, **kwargs)

    @property
    def password(self):
        # Note: Crypto.Cipher cannot be imported in app engine.
        from Crypto.Cipher import AES
        password_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.password_iv)
        return password_aes_cfb.decrypt(self._password)

    @password.setter
    def password(self, password):
        from Crypto.Cipher import AES
        from Crypto.Util import randpool
        rp = randpool.RandomPool()

        self.password_iv = rp.get_bytes(16)
        logging.info("Setting password %s" % self.password_iv)

        password_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.password_iv)
        self._password = password_aes_cfb.encrypt(password)

    @property
    def username(self):
        # Note: Crypto.Cipher cannot be imported in app engine.
        from Crypto.Cipher import AES
        username_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.username_iv)
        return username_aes_cfb.decrypt(self._username)

    @username.setter
    def username(self, username):
        from Crypto.Cipher import AES
        from Crypto.Util import randpool
        rp = randpool.RandomPool()

        self.username_iv = rp.get_bytes(16)
        logging.info("Setting username %s" % self.username_iv)
        logging.warning("3")
        logging.warning(self.__dict__)

        username_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.username_iv)
        self._username = username_aes_cfb.encrypt(username)

    @classmethod
    def get_by_ad_network_name(cls, account, ad_network_name):
        return cls.get_by_key_name('k:%s:%s' % (account.key(), ad_network_name))

class AdNetworkAppMapper(db.Model): #(ad_network_name,publisher_id)
    ad_network_name = db.StringProperty(required=True)
    publisher_id = db.StringProperty(required=True)

    ad_network_login = db.ReferenceProperty(AdNetworkLoginCredentials,
            collection_name='ad_network_app_mappers')
    application = db.ReferenceProperty(App, collection_name=
            'ad_network_app_mappers')

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

        stats = AdNetworkScrapeStats.all().filter('ad_network_app_mapper =',
                self).get()

        return stats == None

class AdNetworkScrapeStats(db.Model): #(AdNetworkAppMapper, date)
    ad_network_app_mapper = db.ReferenceProperty(AdNetworkAppMapper,
                                             collection_name='ad_network_stats')
    date = db.DateProperty(required=True)

    # stats info for a specific day
    revenue = db.FloatProperty(default=0.0)
    attempts = db.IntegerProperty(default=0)
    impressions = db.IntegerProperty(default=0)
    clicks = db.IntegerProperty(default=0)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            mapper = kwargs.get('ad_network_app_mapper', None)
            mapper = mapper.key() if mapper else '*'
            kwargs['key_name'] = ('k:%s:%s' % (mapper, kwargs['date'].
                    strftime('%Y-%m-%d')))
        super(AdNetworkScrapeStats, self).__init__(*args, **kwargs)

    @property
    def cpm(self):
        return self.revenue / self.impressions * 1000

    @property
    def fill_rate(self):
        return self.impressions / float(self.attempts)

    @property
    def cpc(self):
        return self.revenue / self.clicks

    @property
    def ctr(self):
        return self.clicks / float(self.impressions)

    @classmethod
    def get_by_app_mapper_and_day(cls, app_mapper, day):
        return cls.get_by_key_name('k:%s:%s' % (app_mapper.key(),
            day.strftime('%Y-%m-%d')))

    @classmethod
    def get_by_app_mapper_and_days(cls, app_mapper_key, days):
        stats_list = cls.get_by_key_name(['k:%s:%s' % (app_mapper_key,
            day.strftime('%Y-%m-%d')) for day in days])
        final_stats_list = []
        for stats, day in zip(stats_list, days):
            if not stats:
                stats = AdNetworkScrapeStats(date=day)
            final_stats_list.append(stats)
        return final_stats_list


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
