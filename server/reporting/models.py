from google.appengine.ext import db

from publisher.models import Site
import datetime
import md5
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
	def sitestats_for_today(c, site):
		return SiteStats.sitestats_for_day(site, SiteStats.today())

	@classmethod
	def sitestats_for_day(c, site, d):
		return SiteStats.get_or_insert(SiteStats.get_key(site.key(), None, d).name(), site=site, date=d)

	@classmethod
	def stats_for_day(c, owner, d):
		return SiteStats.get_or_insert(SiteStats.get_key(None, owner.key(), d).name(), owner=owner, date=d)
		
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
  	
	def __repr__(self):
	  return "%s (site)\t%s (%s)\t%d\t%d\t%d" % (self.site.key() if self.site else '-', self.owner.key() if self.owner else '-', type(self.owner), self.request_count, self.impression_count, self.click_count)
		
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