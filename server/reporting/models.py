from google.appengine.api.datastore_types import Key

from google.appengine.ext import db
from google.appengine.ext import blobstore
from publisher.models import Site
from advertiser.models import Creative
from account.models import Account
from common.utils import simplejson
from common.utils.timezones import Pacific_tzinfo

import datetime
import hashlib
import logging
import time

DEFAULT_COUNTRY = 'XX'

# Geo request type
GEO_REQUEST_COUNT = 'request_count'
GEO_IMPRESSION_COUNT = 'impression_count'
GEO_CLICK_COUNT = 'click_count'
GEO_CONVERSION_COUNT = 'conversion_count'
GEO_COUNTS = [GEO_REQUEST_COUNT,GEO_IMPRESSION_COUNT,GEO_CLICK_COUNT,GEO_CONVERSION_COUNT]


class BlobLog(db.Model):

    date = db.DateProperty()
    blob_key = db.StringProperty()
    account = db.StringProperty()

    def __init__(self, **kwargs):
        date = kwargs.get('date', None)
        account = kwargs.get('account', None)

        date_str = date.strftime('%y%m%d') if date else 'None'
        account_str = account or 'None'

        key_name = 'blobkey:%s:%s' % (date_str, account_str)
        return super(BlobLog, self).__init__(key_name=key_name, **kwargs)


class StatsModel(db.Expando):

    publisher = db.ReferenceProperty(collection_name='publisher_stats')
    advertiser = db.ReferenceProperty(collection_name='advertiser_stats')
    account = db.ReferenceProperty(Account,collection_name='account_stats')

    date_hour = db.DateTimeProperty() # modulo to hour or day
    date = db.DateTimeProperty()
    month = db.DateTimeProperty()

    country = db.StringProperty() # two letter country code

    request_count = db.IntegerProperty(default=0)
    impression_count = db.IntegerProperty(default=0)
    click_count = db.IntegerProperty(default=0)
    conversion_count = db.IntegerProperty(default=0)


    # uniq user counts
    user_count = db.IntegerProperty(default=0) # NOTE: name change
    request_user_count = db.IntegerProperty(default=0)
    impression_user_count = db.IntegerProperty(default=0)
    click_user_count = db.IntegerProperty(default=0)

    # List of requests, useful for debugging
    reqs = db.ListProperty(str,indexed=False)

    # total revenue (cost)
    revenue = db.FloatProperty(default=float(0))

    # offline
    offline = db.BooleanProperty(default=False)

    # mobile device and os info
    brand_name = db.StringProperty()
    marketing_name = db.StringProperty() # if marketing_name field is blank from WURFL search, the model_name field is used instead
    device_os = db.StringProperty()
    device_os_version = db.StringProperty()

    include_geo = True

    @classmethod
    def from_json(cls,string):
        props = simplejson.loads(string)
        attrs = {}
        for k,p in cls.properties().iteritems():
            if k in props:
                if isinstance(p,(db.DateTimeProperty, db.DateProperty)):
                    attrs[k] = datetime.datetime.fromtimestamp(float(props[k]))
                else:
                    attrs[k] = p.make_value_from_form(props[k])
                del props[k]

        for k in props:
            attrs[str(k)] = int(props[k])

        return StatsModel(**attrs)



    def to_json(self):
        SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list, Key)

        props = {}
        for k,p in self.properties().iteritems():
            value = getattr(self,'_%s'%k)
            if not value:
                continue
            if isinstance(value, SIMPLE_TYPES):
                props[k] = str(value)
            elif isinstance(value, (datetime.datetime, datetime.date)):
                props[k] = str(time.mktime(value.timetuple()))
            elif isinstance(value, db.Model):
                props[k] = str(value.key())

        # dynamic properties are all ints
        for k in self.dynamic_properties():
            props[k] = str(getattr(self,k))

        return simplejson.dumps(props)

    @property
    def attempt_count(self):
        if self._advertiser:
            return self.request_count
        return 0

    def __init__(self, parent=None, key_name=None, ad_network_stats=None, **kwargs):
        if not key_name and not kwargs.get('key', None):

            # rewrite the publisher, advertiser in case they are strings or unicode to db.Key()
            publisher = kwargs.get('publisher', None)
            advertiser = kwargs.get('advertiser', None)
            publisher = self._force_key(publisher)
            advertiser = self._force_key(advertiser)
            account = kwargs.get('account', None)
            account = self._force_key(account)
            offline = kwargs.get('offline', False)
            country = kwargs.get('country', None)
            if country:
                country = country.upper()

            kwargs.update(publisher=publisher,advertiser=advertiser,account=account,country=country)

            brand_name = kwargs.get('brand_name', None)
            marketing_name = kwargs.get('marketing_name', None)
            device_os = kwargs.get('device_os', None)
            device_os_version = kwargs.get('device_os_version', None)

            date = kwargs.get('date',None)
            date_hour = kwargs.get('date_hour',None)
            month = kwargs.get('month',None)

            key_name = self.get_key_name(publisher=publisher,
                                         advertiser=advertiser,
                                         account=account,
                                         date=date,
                                         date_hour=date_hour,
                                         month=month,
                                         country=country,
                                         brand_name=brand_name,
                                         marketing_name=marketing_name,
                                         device_os=device_os,
                                         device_os_version=device_os_version,
                                         offline=offline)

        # Translation between AdNetworkStats and StatsModel stats
        AD_NETWORK_STATS = {'revenue': 'revenue',
                            'attempts': 'request_count',
                            'impressions': 'impression_count',
                            'clicks': 'click_count'}
        if ad_network_stats:
            kwargs['date'] = datetime.datetime.combine(ad_network_stats.date,
                    datetime.time())
            kwargs['_advertiser'] = True
            for stat in AD_NETWORK_STATS.keys():
                kwargs[AD_NETWORK_STATS[stat]] = getattr(ad_network_stats, stat)

        return super(StatsModel,self).__init__(parent=parent,key_name=key_name,**kwargs)


    def __eq__(self, other):
        return self._account == other._account \
           and self._publisher == other._publisher \
           and self._advertiser == other._advertiser \
           and self.date == other.date \
           and self.request_count == other.request_count \
           and self.impression_count == other.impression_count \
           and self.click_count == other.click_count \
           and self.conversion_count == other.conversion_count \
           and self.revenue == other.revenue


    def update_geo(self,country,geo_type,value):
        # update dynamic properties
        if not geo_type in GEO_COUNTS:
            raise Exception("Invalid Geo Count Type")
        attribute = "%s_country_%s"%(country,geo_type) # e.g. US_country_request_count
        setattr(self,attribute,value)

    def get_geo(self,country,geo_type):
        if not geo_type in GEO_COUNTS:
            raise Exception("Invalid Geo Count Type")
        attribute = "%s_country_%s"%(country,geo_type)
        return getattr(self,attribute,0)

    def get_countries(self):
        countries = set()
        for prop in self.dynamic_properties():
            parts = prop.split('_country_')
            if len(parts) > 1:
                countries.add(parts[0])
        return list(countries)

    def __add__(self,s):
        include_geo = s.include_geo and self.include_geo
        attributes = dict(parent=self.parent_key() or s.parent_key(),
                          key_name=self.key().name() or self.key.name(),
                          publisher=StatsModel.publisher.get_value_for_datastore(self) or StatsModel.publisher.get_value_for_datastore(s),
                          account=StatsModel.account.get_value_for_datastore(self) or StatsModel.account.get_value_for_datastore(s),
                          date=self.date or s.date,
                          date_hour=self.date_hour or s.date_hour,
                          month=self.month or s.month,
                          country=self.country or s.country,
                          brand_name=self.brand_name or s.brand_name,
                          marketing_name=self.marketing_name or s.marketing_name,
                          device_os=self.device_os or s.device_os,
                          device_os_version=self.device_os_version or s.device_os_version,
                          request_count=self.request_count + s.request_count,
                          impression_count=self.impression_count + s.impression_count,
                          click_count=self.click_count + s.click_count,
                          conversion_count=self.conversion_count + s.conversion_count,
                          revenue=self.revenue + s.revenue,
                          user_count=max(self.user_count, s.user_count), # TODO: takes the maximum user count over the period (high water mark)
                          request_user_count=self.request_user_count,
                          impression_user_count=self.impression_user_count,
                          click_user_count=self.click_user_count,
                          reqs=self.reqs+s.reqs,
                          offline=self.offline)
        advertiser = StatsModel.advertiser.get_value_for_datastore(self) or \
                StatsModel.advertiser.get_value_for_datastore(s)
        # If an advertiser exists for self or s set it
        if not isinstance(advertiser, bool):
            attributes['advertiser'] = advertiser
        obj = StatsModel(**attributes)
        obj.include_geo = include_geo

        # add dynamic geo properties
        if include_geo:
            countries_self = self.get_countries()
            countries_s = s.get_countries()
            # all countries
            countries = set(countries_self).union(set(countries_s))
            for country in countries:
                for geo_count in GEO_COUNTS:
                    attribute = '%s_country_%s'%(country,geo_count)
                    # obj.US_country_request_count = self.US_country_request_count + s.US_country_request_count
                    new_value = getattr(self,attribute,0) + getattr(s,attribute,0)
                    setattr(obj,attribute,new_value)

        return obj

    def __unicode__(self):
        return str(self)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return  "StatsModel(date=%s, pub=%s, adv=%s, account=%s, \
country=%s, brand_name=%s, marketing_name=%s, device_os=%s, device_os_version=%s, \
offline=%s, %s,%s,%s,%s)" % (self.date or self.date_hour,
                                              StatsModel.publisher.get_value_for_datastore(self),
                                              StatsModel.advertiser.get_value_for_datastore(self),
                                              StatsModel.account.get_value_for_datastore(self),
                                              self.country,
                                              self.brand_name,
                                              self.marketing_name,
                                              self.device_os,
                                              self.device_os_version,
                                              self.offline,
                                              self.request_count,
                                              self.impression_count,
                                              self.click_count,
                                              self.conversion_count,
                                              )


    @classmethod
    def get_key_name(cls, publisher=None, advertiser=None, account=None,
                     date_hour=None, date=None, month=None,
                     country=None, brand_name=None, marketing_name=None, device_os=None, device_os_version=None,
                     offline=False, date_fmt='date'):
        if publisher or advertiser or date_hour or date or month:
            key_name_str = ''

            if isinstance(publisher, db.Model):
                publisher = publisher.key()
            if isinstance(advertiser, db.Model):
                advertiser = advertiser.key()
            key_name_str += 'k:%s:%s' % (publisher or '', advertiser or '')

            # these parameters must all be appended if any of them has a value (neither None nor empty-string)
            if country or brand_name or marketing_name or device_os or device_os_version:
                key_name_str += ':%s' % ((country or '').upper())
                key_name_str += ':%s' % (brand_name or '')
                key_name_str += ':%s' % (marketing_name or '')
                key_name_str += ':%s' % (device_os or '')
                key_name_str += ':%s' % (device_os_version or '')

            if date:
                if date_fmt == 'date':
                    date_str = date.strftime('%y%m%d')
                elif date_fmt == 'date_hour':
                    date_str = date.strftime('%y%m%d%H')
                elif date_fmt == 'month':
                    date_str = date.strftime('%y%m')
            elif date_hour and not date_fmt == 'date_hour':
                date_str = date_hour.strftime('%y%m%d%H')

            elif month and not date_fmt == 'month':
                date_str = month.strftime('%y%m')

            key_name_str += ':%s' % (date_str)
            return key_name_str

        else:
            if offline:
                return 'k:%s_offline'%account
            else:
                return 'k:%s'%account


    @classmethod
    def get_key(cls, publisher, advertiser, account=None,
                date_hour=None, date=None, month=None,
                country=None, brand_name=None, marketing_name=None, device_os=None, device_os_version=None,
                offline=False):
        return db.Key.from_path(cls.kind(),
                                cls.get_key_name(publisher=publisher, advertiser=advertiser, account=account,
                                                 date_hour=date_hour, date=date, month=month,
                                                 country=country,
                                                 brand_name=brand_name, marketing_name=marketing_name,
                                                 device_os=device_os, device_os_version=device_os_version,
                                                 offline=offline))

    def _force_key(self,prop):
        if prop:
            prop = db.Key(prop) if isinstance(prop,(str,unicode)) else prop
        return prop

    @classmethod
    def today(c):
      return datetime.datetime.now(Pacific_tzinfo()).date()

    @classmethod
    def today(c):
      return datetime.datetime.now(Pacific_tzinfo()).date()

    @classmethod
    def lastdays(c, n=7, omit=0):
        today = c.today() - datetime.timedelta(days=omit)    # Set omit=1 to eliminates partial days contributing to totals or appearing in graphs
        days = [today - datetime.timedelta(days=x) for x in range(0, n)]
        days.reverse()
        return days

    @classmethod
    def get_days(c, start, n=7):
        try:
            days = [start + datetime.timedelta(days=x) for x in range(0,n)]
            return days
        except:
            return c.lastdays(n)

    @property
    def fill_rate(self):
        if self.request_count > 0:
            return self.impression_count / float(self.request_count)
        else:
            return 0

    @property
    def ctr(self):
        if self.impression_count > 0:
            return float(self.click_count) / float(self.impression_count)
        else:
            return 0

    @property
    def conv_rate(self):
        if self.click_count > 0 and self.conversion_count > 0:
            return self.conversion_count / float(self.click_count)
        else:
            return 0

    @property
    def only_date(self):
        #we just want the date, not the time
        if self.date:
            return self.date.date()


    def get_cpm(self):
        if hasattr(self, '_cpm'): return self._cpm

        if self.impression_count > 0:
            return self.revenue * 1000 / float(self.impression_count)
        else:
            return 0

    def set_cpm(self, value):
        self._cpm = value

    cpm = property(get_cpm, set_cpm)

    def get_percent_delivered(self):
        if hasattr(self, '_percent_delivered'): return self._percent_delivered
        return None

    def set_percent_delivered(self, value):
        self._percent_delivered = value

    percent_delivered = property(get_percent_delivered, set_percent_delivered)

    def get_pace(self):
        if hasattr(self, '_pace'): return self._pace
        return None

    def set_pace(self, value):
        self._pace = value

    pace = property(get_pace, set_pace)

    def get_pace_type(self):
        if hasattr(self, '_pace_type'): return self._pace_type

    def set_pace_type(self, value):
        self._pace_type = value

    pace_type = property(get_pace_type, set_pace_type)

    def get_status(self):
        if hasattr(self, '_status'): return self._status
        return None

    def set_status(self, value):
        self._status = value

    status = property(get_status, set_status)

    def get_on_schedule(self):
        if hasattr(self, '_on_schedule'): return self._on_schedule
        return None

    def set_on_schedule(self, value):
        self._on_schedule = value

    on_schedule = property(get_on_schedule, set_on_schedule)

    @property
    def cpc(self):
        if self.click_count > 0:
            return self.revenue / float(self.click_count)
        else:
            return 0

    @property
    def cpa(self):
        if self.conversion_count > 0:
            return self.revenue / float(self.conversion_count)
        else:
            return 0

    @property
    def is_rollup(self):
        #Make sure all values are set, any values not set imply a rollup on that value
        if self.publisher and self.advertiser and self.date_hour and self.country and self.brand_name and self.marketin_name and self.device_os and self.device_os_version:
            return False
        else:
            #If publisher isn't an adunit or advertiser isn't a creative
            if self.publisher.kind() != Site.kind() or self.advertiser.kinds() != Creative.kind():
                return False
            return True


    def _dict_properties(self):
        model_props = self.properties().keys()
        pseudo_props = ['attempt_count', 'cpa', 'cpc', 'cpm', 'fill_rate', \
                'pace', 'pace_type', 'conv_rate', 'ctr', \
                'on_schedule', 'status']
        return model_props + pseudo_props

    def to_dict(self):
        properties = self._dict_properties()
        d = {}
        for prop_name in properties:
            value = getattr(self, '_%s'%prop_name, None)
            if value is None:
                value = getattr(self, '%s'%prop_name, None)
            if value is not None:
                if isinstance(value, db.Model):
                    value = str(value.key())
                if isinstance(value, db.Key):
                    value = str(value)
                if isinstance(value, datetime.datetime):
                    value = str(value)
                d[prop_name] = value
        return d
#
# Tracks statistics for a site for a particular day - clicks and impressions are aggregated
# into this object
#
class SiteStats(db.Model):
  site = db.ReferenceProperty(Site)
  owner = db.ReferenceProperty()
  date = db.DateProperty()

  @property
  def str_date( self ):
      if self.date:
          return self.date.strftime( '%d/%m/%y' )
      else:
          return "No date"

  # impressions and clicks
  request_count = db.IntegerProperty(default=0)
  impression_count = db.IntegerProperty(default=0)
  click_count = db.IntegerProperty(default=0)
  unique_user_count = db.IntegerProperty(default=0)

  # total revenue (cost)
  revenue = db.FloatProperty(default=float(0))

  # conversion information
  conversion_count = db.IntegerProperty()


  _geo_requests_json = db.TextProperty()
  _geo_impressions_json = db.TextProperty()
  _geo_clicks_json = db.TextProperty()
  _geo_revenues_json = db.TextProperty()
  _geo_users_json = db.TextProperty()

  @property
  def geo_requests(self):
    if not hasattr(self,'_geo_requests'):
      from django.utils import simplejson
      if self._geo_requests_json:
        self._geo_requests = simplejson.loads(self._geo_requests_json)
      else:
        self._geo_requests = {}
    return self._geo_requests

  @property
  def geo_request_dict(self):
    if not hasattr(self,'_geo_request_dict'):
      if self._geo_requests_json:
        self._geo_request_dict = self.geo_requests
      else:
        self._geo_request_dict = {}
    return self._geo_request_dict

  def put(self,*args,**kwargs):
    from django.utils import simplejson
    self._geo_requests_json = simplejson.dumps(getattr(self,'_geo_request_dict',{}))
    return super(SiteStats,self).put(*args,**kwargs)

  @classmethod
  def today(c):
    return datetime.datetime.now(Pacific_tzinfo()).date()

  @classmethod
  def get_key(c, site_key, owner_key, date):
    return db.Key.from_path("SiteStats", "%s:%s:%s" % (site_key if site_key else '', owner_key if owner_key else '', str(date)))

  @classmethod
  def lastdays(c, n=7, omit=0):
    today = c.today() - datetime.timedelta(days=omit)    # Set omit=1 to eliminates partial days contributing to totals or appearing in graphs
    days = [today - datetime.timedelta(days=x) for x in range(0, n)]
    days.reverse()
    return days

  @classmethod
  def get_days(c, start, n=7):
    try:
      days = [start + datetime.timedelta(days=x) for x in range(0,n)]
      return days
    except:
      return c.lastdays(n)

  @classmethod
  def sitestats_for_today(c, site):
    return SiteStats.sitestats_for_day(site, SiteStats.today())

  @classmethod
  def sitestats_for_day(c, site, d):
    return SiteStats.get_or_insert(SiteStats.get_key(site.key(), None, d).name(), site=site, date=d)

  @classmethod
  def stats_for_day(c, owner, d):
    return SiteStats.get_or_insert(SiteStats.get_key(None, owner.key(), d).name(), owner=owner, date=d)

  @classmethod
  def rollup_for_day(c, owners, d):
    a = map(lambda s: s or SiteStats(), db.get([SiteStats.get_key(None, owner.key(), d) for owner in owners]))
    return reduce(lambda x, y: x+y, a, SiteStats())

  @classmethod
  def rollup_site_for_day(c, sites, d):
    a = map(lambda s: s or SiteStats(), [SiteStats.gql("where site = :1 and owner = NULL and date = :2", s, d).get() for s in sites])
    return reduce(lambda x, y: x+y, a, SiteStats())

  @classmethod
  def sitestats_for_days(c, site, days):
    keys = [SiteStats.get_key(site.key(), None, d) for d in days]
    # TODO: make all the map() into more python-like
    return [s or SiteStats() for s in SiteStats.get(keys)]
    # return map(lambda s: s or SiteStats(), SiteStats.get(keys))

  @classmethod
  def stats_for_days(c, owner, days):
    keys = [SiteStats.get_key(None, owner.key(), d) for d in days]
    return map(lambda s: s or SiteStats(), SiteStats.get(keys))

  @classmethod
  def stats_for_day_with_qualifier(c, owner, site, d):
    return SiteStats.get_or_insert(SiteStats.get_key(site.key(), owner.key(), d).name(), owner=owner, site=site, date=d)

  @classmethod
  def stats_for_days_with_qualifier(c, owner, site, days):
    return map(lambda s: s or SiteStats(), db.get([SiteStats.get_key(site.key(), owner.key(), d) for d in days]))

  def fill_rate(self):
    return self.impression_count / float(self.request_count)

  def ctr(self):
    if self.impression_count > 0:
      return self.click_count / float(self.impression_count)

  def conv_rate(self):
    if self.click_count > 0 and self.conversion_count > 0:
      return self.conversion_count / float(self.click_count)
    else:
      return None

  def cpm(self):
    if self.impression_count > 0:
      return self.revenue * 1000 / float(self.impression_count)

  def cpc(self):
    if self.click_count > 0:
      return self.revenue / float(self.click_count)

  def cpa(self):
    if self.conversion_count > 0:
      return self.revenue / float(self.conversion_count)
    else:
      return None

# Turn the previous functions into properties of the class so they can be read as variables
# ( useful for cool map shit )

  @property
  def fill_rate_p( self ):
      return self.fill_rate()

  @property
  def cpa_p( self ):
      return self.cpa()

  @property
  def ctr_p( self ):
      return self.ctr()

  @property
  def conv_rate_p( self ):
      return self.conv_rate()

  @property
  def cpm_p( self ):
      return self.cpm()

  @property
  def cpc_p( self ):
      return self.cpc()

  def add_impression(self):
    self.impression_count += 1
    self.put()

  def add_click(self):
    self.click_count += 1
    self.put()

  def add_click_with_revenue(self, revenue):
    self.click_count += 1
    self.revenue += revenue
    self.put()

  def add_user(self,u):
    if hasattr(self,'unique_user_set'):
      self.unique_user_set.add(u)
      self.unique_user_count = len(self.unique_user_set)
    else:
      self.unique_user_set = set([u])
      self.unique_user_count = 1

  def __add__(self, s):
    return SiteStats(site=self.site,
      owner=self.owner,
      date=self.date,
      request_count = self.request_count + s.request_count,
      impression_count = self.impression_count + s.impression_count,
      click_count = self.click_count + s.click_count,
      revenue = self.revenue + s.revenue,
      unique_user_count = self.unique_user_count + s.unique_user_count, # TODO: we need to de-dupe this!
      conversion_count = self.conversion_count + s.conversion_count if self.conversion_count and s.conversion_count else None )

  def __repr__(self):
    from django.utils import simplejson
    self._geo_requests_json = simplejson.dumps(getattr(self,'_geo_request_dict',{}))
    try:
      return "SiteStats{site=%s, owner=%s(%s), R=%d/I=%d/C=%d/R=%.2f, users=%d, geo=%s}" % (self.site.key() if self.site else "None", self.owner.__class__.__name__ if self.owner else '',self.owner.key() if self.owner else "None", self.request_count, self.impression_count, self.click_count, self.revenue, self.unique_user_count,self._geo_requests_json)
    except:
      return "SiteStats{broken!}"

#
# This contains information about a particular user
#
class UserStats(db.Model):
  device_id = db.StringProperty()
  last_updated = db.DateTimeProperty()

  ll = db.StringProperty()

  keywords = db.StringListProperty()

  def __repr__(self):
    return "%s\tll=%s,q=%s" % (self.device_id, self.ll, self.keywords)
