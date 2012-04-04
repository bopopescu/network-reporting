import sys
import os
import logging
from google.appengine.ext import db

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from account.models import Account
from publisher.models import App

KEY = 'V("9L^4z!*QCF\%"7-/j&W}BZmDd7o.<'

STAT_NAMES = ('revenue', 'attempts', 'impressions', 'clicks')
CALCULATED_STAT_NAMES = ('cpm', 'fill_rate', 'cpc', 'ctr')
MANAGEMENT_STAT_NAMES = ('found', 'updated', 'attempted_logins')
FAILED_LOGINS = 'failed_logins'

class LoginStates:
    """
    Login credential states
    """
    NOT_SETUP = 0
    PULLING_DATA = 1
    WORKING = 2
    ERROR = 3


class AdNetworkLoginCredentials(db.Model):
    """
    key:
    (account,ad_network_name)
    """
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

    state = db.IntegerProperty(default=LoginStates.NOT_SETUP)

    deleted = db.BooleanProperty(default=False)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s:%s' % (kwargs['account'].key(),
                kwargs['ad_network_name']))
        super(AdNetworkLoginCredentials, self).__init__(*args, **kwargs)
        if 'username' in kwargs and not kwargs.get('debug', False):
            self.username = kwargs['username']
        if 'password' in kwargs and not kwargs.get('debug', False):
            self.password = kwargs['password']

    def get_username(self):
        # Note: Crypto.Cipher cannot be imported in app engine.
        from Crypto.Cipher import AES
        username_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.username_iv)
        return username_aes_cfb.decrypt(self._username)

    def set_username(self, username):
        from Crypto.Cipher import AES
        from Crypto.Util import randpool
        rp = randpool.RandomPool()

        self.username_iv = rp.get_bytes(16)
        username_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.username_iv)
        self._username = username_aes_cfb.encrypt(username)

    def get_password(self):
        # Note: Crypto.Cipher cannot be imported in app engine.
        from Crypto.Cipher import AES
        password_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.password_iv)
        return password_aes_cfb.decrypt(self._password)

    def set_password(self, password):
        from Crypto.Cipher import AES
        from Crypto.Util import randpool
        rp = randpool.RandomPool()

        self.password_iv = rp.get_bytes(16)
        password_aes_cfb = AES.new(KEY, AES.MODE_CFB, self.password_iv)
        self._password = password_aes_cfb.encrypt(password)

    username = property(get_username, set_username)

    password = property(get_password, set_password)

    @classmethod
    def get_by_ad_network_name(cls, account, ad_network_name):
        return cls.get_by_key_name('k:%s:%s' % (account.key(), ad_network_name))

class AdNetworkAppMapper(db.Model):
    """
    key:
    (ad_network_name,publisher_id)
    """
    ad_network_name = db.StringProperty(required=True)
    publisher_id = db.StringProperty(required=True)

    ad_network_login = db.ReferenceProperty(AdNetworkLoginCredentials,
            collection_name='ad_network_app_mappers')
    # application property cannot be called app since it's a reseverd word
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

class AdNetworkStats(db.Model):
    date = db.DateProperty()

    # stats info for a specific day
    revenue = db.FloatProperty(default=0.0)
    attempts = db.IntegerProperty(default=0)
    impressions = db.IntegerProperty(default=0)
    clicks = db.IntegerProperty(default=0)

    def __add__(self,
                stats):
        """
        stats1 = self + stats
        """
        for stat in STAT_NAMES:
            # example: self.revenue += stats.revenue
            setattr(self, stat, getattr(self, stat) + getattr(stats, stat))
        self.date = self.date or stats.date
        return self

    def __sub_(self,
                stats):
        """
        stats1 = self - stats
        """
        for stat in STAT_NAMES:
            # example: self.revenue -= stats.revenue
            setattr(self, stat, getattr(self, stat) - getattr(stats, stat))
        return self

    @property
    def cpm(self):
        if self.impressions:
            return self.revenue / self.impressions * 1000
        return 0.0

    @property
    def fill_rate(self):
        if self.attempts:
            # If this instance is being used as a roll up
            if hasattr(self, 'fill_rate_impressions'):
                return self.fill_rate_impressions / \
                        float(self.attempts)
            return self.impressions / float(self.attempts)
        return 0.0

    @property
    def cpc(self):
        if self.clicks:
            return self.revenue / self.clicks
        return 0.0

    @property
    def ctr(self):
        if self.impressions:
            return self.clicks / float(self.impressions)
        return 0.0

    @property
    def dict_(self):
        """
        Override __dict__ property to return a dict of the stats.

        Basically it removes all the app engine entity crap and includes the
        calculated properties.
        """
        stats_dict = {}
        stats_dict['date'] = getattr(self, 'date', None)
        for stat in STAT_NAMES:
            stats_dict[stat] = getattr(self, stat)
        for stat in CALCULATED_STAT_NAMES:
            stats_dict[stat] = getattr(self, stat)
        return stats_dict

class AdNetworkScrapeStats(AdNetworkStats):
    """
    key:
    (AdNetworkAppMapper, date)
    """
    ad_network_app_mapper = db.ReferenceProperty(AdNetworkAppMapper,
            collection_name='ad_network_stats')

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            if kwargs.get('ad_network_app_mapper', None) and kwargs.get('date',
                    None):
                kwargs['key_name'] = ('k:%s:%s' % (kwargs[
                    'ad_network_app_mapper'].key(),
                    kwargs['date'].strftime('%Y-%m-%d')))
        super(AdNetworkScrapeStats, self).__init__(*args, **kwargs)

    @classmethod
    def get_by_app_mapper_and_day(cls, app_mapper, day):
        return cls.get_by_key_name('k:%s:%s' % (app_mapper.key(),
            day.strftime('%Y-%m-%d')))

    @classmethod
    def get_by_app_mapper_and_days(cls, app_mapper_key, days,
            include_last_day=False):
        stats_list = cls.get_by_key_name(['k:%s:%s' % (app_mapper_key,
            day.strftime('%Y-%m-%d')) for day in days])
        final_stats_list = []
        for stats, day in zip(stats_list, days):
            if not stats:
                stats = AdNetworkScrapeStats(date=day)
            final_stats_list.append(stats)
        if include_last_day:
            filtered_stats = [stats for stats in stats_list if stats != None]
            if filtered_stats:
                return final_stats_list, max(filtered_stats, key=lambda stats:
                        stats.date).date
            return final_stats_list, None
        return final_stats_list

class AdNetworkNetworkStats(AdNetworkStats):
    """
    key:
    (Account, ad_network_name, date)
    """
    account = db.ReferenceProperty(Account, required=True,
            collection_name='ad_network_network_stats')
    ad_network_name = db.StringProperty(required=True)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            if kwargs.get('account', None) and kwargs.get('ad_network_name', \
                    None) and kwargs.get('date', None):
                kwargs['key_name'] = ('k:%s:%s:%s' % (kwargs[
                    'account'].key(), kwargs['ad_network_name'],
                    kwargs['date'].strftime('%Y-%m-%d')))
        super(AdNetworkNetworkStats, self).__init__(*args, **kwargs)

    @classmethod
    def get_by_network_and_day(cls, account, network, day):
        return cls.get_by_key_name('k:%s:%s:%s' % (account.key(),
            network, day.strftime('%Y-%m-%d')))

class AdNetworkAppStats(AdNetworkStats):
    """
    key:
    (Account, App, date)
    """
    account = db.ReferenceProperty(Account, required=True,
            collection_name='ad_network_app_stats')
    application = db.ReferenceProperty(App, required=True,
            collection_name='ad_network_stats')

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            if kwargs.get('account', None) and kwargs.get('application', \
                    None) and kwargs.get('date', None):
                kwargs['key_name'] = ('k:%s:%s:%s' % (kwargs[
                    'account'].key(), kwargs['application'].key(),
                    kwargs['date'].strftime('%Y-%m-%d')))
        super(AdNetworkAppStats, self).__init__(*args, **kwargs)

    @classmethod
    def get_by_app_and_day(cls, account, app, day):
        return cls.get_by_key_name('k:%s:%s:%s' % (account.key(),
            app.key(), day.strftime('%Y-%m-%d')))

class AdNetworkManagementStats(db.Model): #(date)
    """
    key:
    (date)
    """
    ad_network_name = db.StringProperty(required=True)
    date = db.DateProperty(required=True)

    found = db.IntegerProperty(default=0)
    updated = db.IntegerProperty(default=0)

    attempted_logins = db.IntegerProperty(default=0)
    failed_logins = db.StringListProperty(default=[])

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s:%s' % (kwargs['ad_network_name'],
                kwargs['date'].strftime('%Y-%m-%d')))
        super(AdNetworkManagementStats, self).__init__(*args, **kwargs)

    @property
    def success_rate(self):
        if attempted_logins:
            return attempted_logins - len(failed_logins) / \
                    float(attempted_logins)
        return 0

    @classmethod
    def get_by_day(cls,ad_network_name, day):
        return cls.get_by_key_name('k:%s:%s' % (ad_network_name,
            day.strftime('%Y-%m-%d')))

    @classmethod
    def get_by_days(cls, ad_network_name, days):
        return [stats for stats in cls.get_by_key_name(['k:%s:%s' %
            (ad_network_name, day.strftime('%Y-%m-%d')) for day in days])
            if stats != None]

