from google.appengine.ext import db

from publisher.models import Site
from account.models import Account

import datetime
import hashlib
import logging

class Pacific_tzinfo(datetime.tzinfo):
    """Implementation of the Pacific timezone."""
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-8) + self.dst(dt)

    def _FirstSunday(self, dt):
        """First Sunday on or after dt."""
        return dt + datetime.timedelta(days=(6-dt.weekday()))

    def dst(self, dt):
        # 2 am on the second Sunday in March
        dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 8, 2))
        # 1 am on the first Sunday in November
        dst_end = self._FirstSunday(datetime.datetime(dt.year, 11, 1, 1))

        if dst_start <= dt.replace(tzinfo=None) < dst_end:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(hours=0)
    def tzname(self, dt):
        if self.dst(dt) == datetime.timedelta(hours=0):
            return "PST"
        else:
            return "PDT"


class StatsModel(db.Model):
    publisher = db.ReferenceProperty(collection_name='publisher_stats')
    advertiser = db.ReferenceProperty(collection_name='advertiser_stats')
    account = db.ReferenceProperty(Account,collection_name='account_stats')
    
    date = db.DateTimeProperty() # modulo to hour or day
    
    request_count = db.IntegerProperty(default=0)
    impression_count = db.IntegerProperty(default=0)
    click_count = db.IntegerProperty(default=0)
    conversion_count = db.IntegerProperty(default=0)
    user_count = db.IntegerProperty(default=0)
    
    # List of requests, useful for debugging
    reqs = db.ListProperty(str,indexed=False)
    
    # total revenue (cost)
    revenue = db.FloatProperty(default=float(0))

    # geo information
    _geo_requests_json = db.StringProperty()
    _geo_impressions_json = db.StringProperty()
    _geo_clicks_json = db.StringProperty()
    _geo_revenues_json = db.StringProperty()
    _geo_users_json = db.StringProperty()
    
    
    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key',None):
            
            # rewrite the publisher, advertiser in case they are strings or unicode to db.Key()
            publisher = kwargs.get('publisher',None)
            advertiser = kwargs.get('advertiser',None)            
            publisher = self._force_key(publisher)
            advertiser = self._force_key(advertiser)
            account = kwargs.get('account',None)
            account = self._force_key(account)
            kwargs.update(publisher=publisher,advertiser=advertiser,account=account)


            
            # grab the date and make key name
            date = kwargs.get('date',None)
            date_hour = kwargs.get('date_hour',None)
            
            # if date_hour is used the underlying data is actually just stored in 'date'
            if not date and date_hour:
                kwargs.update(date=date_hour)
            key_name = self.get_key_name(publisher=publisher,
                                         advertiser=advertiser,
                                         date=date,
                                         date_hour=date_hour,
                                         account=account)
        return super(StatsModel,self).__init__(parent=parent,key_name=key_name,**kwargs)
        
    @property
    def date_hour(self):
        return self.date
        
    # @date_hour.setter
    # def date_hour(self,value):
    #     self.date = value
        
    def __add__(self,s):
        return StatsModel(parent=self.parent_key(),
                          key_name=self.key().name(),
                          publisher=StatsModel.publisher.get_value_for_datastore(self),
                          advertiser=StatsModel.advertiser.get_value_for_datastore(self),
                          account=StatsModel.account.get_value_for_datastore(self),
                          date=self.date,
                          request_count=self.request_count + s.request_count,
                          impression_count=self.impression_count + s.impression_count,
                          click_count=self.click_count + s.click_count,
                          conversion_count=self.conversion_count + s.conversion_count,
                          user_count=self.user_count + s.user_count, # TODO: this needs to be deduped
                          reqs=self.reqs+s.reqs,
                         )
               
               
    def __unicode__(self):
        return str(self)           

    def __repr__(self):
        return self.__str__()
                    
    def __str__(self):
        return  "StatsModel(date=%s, pub=%s, adv=%s, account=%s, %s,%s,%s,%s)"%(
                                                          self.date,
                                                          StatsModel.publisher.get_value_for_datastore(self),
                                                          StatsModel.advertiser.get_value_for_datastore(self),    
                                                          StatsModel.account.get_value_for_datastore(self),
                                                          self.request_count,
                                                          self.impression_count,
                                                          self.click_count,
                                                          self.conversion_count,
                                                          )

    
    @classmethod
    def get_key_name(cls,publisher,advertiser,date=None,date_hour=None,account=None):
        if publisher or advertiser or date_hour or date:
            if isinstance(publisher,db.Model):
                publisher = publisher.key()
            if isinstance(advertiser,db.Model):
                advertiser = advertiser.key()    
            
            if date_hour:
                date_str = date_hour.strftime('%y%m%d%H')
            else:
                date_str = date.strftime('%y%m%d')
                
            return 'k:%(publisher)s:%(advertiser)s:%(date)s'%dict(date=date_str,
                                                                  publisher=publisher or '',
                                                                  advertiser=advertiser or '')
        else:
            return 'k:%s'%account    
            
    @classmethod
    def get_key(cls, publisher,advertiser,date,date_hour,account=None):
      return db.Key.from_path(cls.kind(),cls.get_key_name(publisher,advertiser,data,date_hour,account))
            
    def _force_key(self,prop):
        if prop:
            prop = db.Key(prop) if isinstance(prop,(str,unicode)) else prop
        return prop    

# 
# Tracks statistics for a site for a particular day - clicks and impressions are aggregated
# into this object
# 
class SiteStats(db.Model):
  site = db.ReferenceProperty(Site)
  owner = db.ReferenceProperty()
  date = db.DateProperty()

  # impressions and clicks
  request_count = db.IntegerProperty(default=0)
  impression_count = db.IntegerProperty(default=0)
  click_count = db.IntegerProperty(default=0)
  unique_user_count = db.IntegerProperty(default=0)

  # total revenue (cost)
  revenue = db.FloatProperty(default=float(0))

  # conversion information
  conversion_count = db.IntegerProperty()

  _geo_requests_json = db.StringProperty()
  _geo_impressions_json = db.StringProperty()
  _geo_clicks_json = db.StringProperty()
  _geo_revenues_json = db.StringProperty()
  _geo_users_json = db.StringProperty()

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