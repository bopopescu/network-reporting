from google.appengine.ext import db

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from account.models import Account
from publisher.models import App

class AdNetworkLoginCredentials(db.Model): #(account,ad_network_name)
    account = db.ReferenceProperty(Account, required = True,
            collection_name='login_credentials')
    ad_network_name = db.StringProperty(required=True)

    # needed for all networks but mobfox
    username = db.StringProperty()
    password = db.StringProperty()

    # needed for admob
    client_key = db.StringProperty()

    # Special white list for jumptap
    adunit_publisher_ids = db.StringListProperty()

    email = db.BooleanProperty(default = False)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s:%s' % (kwargs['account'].key(),
                    kwargs['ad_network_name']))
        super(AdNetworkLoginCredentials, self).__init__(*args, **kwargs)

    @classmethod
    def kind(self):
        return 'AdNetworkLoginInfo'

    @classmethod
    def get_by_network(self, account, network):
        return self.get_by_key_name('k:%s:%s' % (account.key(), network))

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

class AdNetworkScrapeStats(db.Model): #(AdNetworkAppMapper, date)
    ad_network_app_mapper = db.ReferenceProperty(AdNetworkAppMapper, required=
            True, collection_name='ad_network_stats')
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

class AdNetworkAggregate(db.Model): #(date)
    date = db.DateProperty(required=True)

    # Could be done with the Expando class but probably better to make
    # explicit.

    admob_found = db.IntegerProperty(default=0)
    admob_updated = db.IntegerProperty(default=0)
    admob_mapped = db.IntegerProperty(default=0)
    admob_failed = db.IntegerProperty(default=0)

    jumptap_found = db.IntegerProperty(default=0)
    jumptap_updated = db.IntegerProperty(default=0)
    jumptap_mapped = db.IntegerProperty(default=0)
    jumptap_failed = db.IntegerProperty(default=0)

    iad_found = db.IntegerProperty(default=0)
    iad_updated = db.IntegerProperty(default=0)
    iad_mapped = db.IntegerProperty(default=0)
    iad_failed = db.IntegerProperty(default=0)

    inmobi_found = db.IntegerProperty(default=0)
    inmobi_updated = db.IntegerProperty(default=0)
    inmobi_mapped = db.IntegerProperty(default=0)
    inmobi_failed = db.IntegerProperty(default=0)

    mobfox_found = db.IntegerProperty(default=0)
    mobfox_updated = db.IntegerProperty(default=0)
    mobfox_mapped = db.IntegerProperty(default=0)
    mobfox_failed = db.IntegerProperty(default=0)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = ('k:%s' % kwargs['date'].
                    strftime('%Y-%m-%d'))
        super(AdNetworkAggregate, self).__init__(*args, **kwargs)
