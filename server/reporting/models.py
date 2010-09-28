from google.appengine.ext import db

from publisher.models import Site
import datetime
import md5
import logging

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

  # total revenue (cost)
  revenue = db.FloatProperty(default=float(0))

  # conversion information
  converted_clicks = db.IntegerProperty()
  conversions = db.IntegerProperty()
  
  @classmethod
  def get_key(c, site_key, owner_key=None, date=datetime.datetime.now().date()):
    return db.Key.from_path("SiteStats", "%s:%s:%s" % (site_key if site_key else '', owner_key if owner_key else '', str(date)))

  @classmethod
  def today(c):
    return datetime.datetime.now().date()
    
  @classmethod
  def lastdays(c, n=7):
    today = datetime.date.today() - datetime.timedelta(days=1)    # This eliminates partial days contributing to totals or appearing in graphs
    days = [today - datetime.timedelta(days=x) for x in range(0, n)]
    days.reverse()
    return days

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
  def stats_for_days(c, owner, days):
    return map(lambda s: s or SiteStats(), db.get([SiteStats.get_key(None, owner.key(), d) for d in days]))

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

  def cpm(self):
    if self.impression_count > 0:
      return self.revenue * 1000 / float(self.impression_count)

  def cpc(self):
    if self.click_count > 0:
      return self.revenue / float(self.click_count)

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
    
  def __add__(self, s):
    return SiteStats(site=self.site, 
      owner=self.owner, 
      date=self.date, 
      request_count = self.request_count + s.request_count, 
      impression_count = self.impression_count + s.impression_count,
      click_count = self.click_count + s.click_count,
      revenue = self.revenue + s.revenue,
      converted_clicks = self.converted_clicks + s.converted_clicks if self.converted_clicks and s.converted_clicks else None,
      conversions = self.conversions + s.conversions if self.conversions and s.conversions else None )

  def __repr__(self):
    return "SiteStats{site=%s, owner=%s, %d/%d/%d}" % (self.site.key() if self.site else "None", self.owner.key() if self.owner else "None", self.request_count, self.impression_count, self.click_count)

    
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