#!/usr/bin/env python

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib, md5

from django.utils import simplejson

from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

#
# The main account
#
class Account(db.Model):
	adsense_pub_id = db.StringProperty()
	user = db.UserProperty()
	
	@classmethod
	def current_account(cls):
		u = users.get_current_user()
		return Account.get_or_insert(db.Key.from_path("User", u.user_id()).name(), user=u)
		
		
# An allocation is a way to register an interest in a particular inventory placement
# It can be for a specific number of daily impressions or a fraction of traffic
class Allocation(db.Model):
	name = db.StringProperty()
	allocation_type = db.StringProperty(choices=["adsense", "internal"])
	
# 
# A mobile app, which can have multiple Sites on which ads can be displayed
#
class App(db.Model):
	account = db.ReferenceProperty(Account)
	
	name = db.StringProperty()
	app_type = db.StringProperty(required=True, default="iphone", choices=["iphone", "android", "ipad"])
	description = db.TextProperty()
	url = db.StringProperty(required=True)
	
	t = db.DateTimeProperty(auto_now_add=True)
	
#
# A specific ad placement inside an app
#
class Site(db.Model):
	account = db.ReferenceProperty(Account)
	app = db.ReferenceProperty(App)
	
	name = db.StringProperty(required=True)
	url = db.StringProperty()
	description = db.TextProperty()
	
	# what kind of ad is preferred here
	ad_type = db.StringProperty(required=True, choices=["text", "image"], default="image")
	
	# backfill strategy
	backfill = db.StringProperty(choices=["adsense", "fail", "iAd", "clear"], default="adsense")
	backfill_threshold_cpm = db.FloatProperty(default=0.0)							# will backfill if the eCPM of ads does not exceed this value
	
	# defaults for unprovided context information
	keywords = db.TextProperty()																				# default keywords to use here	
	
	# color scheme
	color_border = db.StringProperty(required=True, default='336699')
	color_bg = db.StringProperty(required=True, default='FFFFFF')
	color_link = db.StringProperty(required=True, default='0000FF')
	color_text = db.StringProperty(required=True, default='000000')
	color_url = db.StringProperty(required=True, default='008000')
	
	# creation time
	t = db.DateTimeProperty(auto_now_add=True)
	
	@classmethod
	def site_by_id(c, id):
		if id.startswith("ca"):
			account = Account.gql("where adsense_pub_id = :1", id).get()
			s = Site.gql("where account = :1", account).get()
		else:
			s = Site.get(id)			
		return s
				
#
# A campaign.  It can run on any number of defined Sites
#	
class Campaign(db.Model):
	name = db.StringProperty()
	description = db.TextProperty()

	budget = db.FloatProperty()		# daily budget in USD
	bid_strategy = db.StringProperty(choices=["cpc", "cpm", "cpa"], default="cpc")
	
	active = db.BooleanProperty(default=True)
	deleted = db.BooleanProperty(default=False)
	
	# Geographic preferences are expressed as string tuples that can match
	# the city, region or country that is resolved via reverse geocode at 
	# request time.  If the list is blank, any value will match. If the list
	# is not empty, the value must match one of the elements of the list.
	# 
	# Valid predicates are:
	# city_name=X,region_name=X,country_name=X
	# region_name=X,country_name=X
	# country_name=X
	# zipcode=X
	#
	# Each incoming request will be matched against all of these combinations
	geo_predicates = db.StringListProperty(default=["country_name=*"])
	
	# Device and platform preferences are listed similarly:
	#
	# model_name=X,brand_name=X
	# brand_name=X,platform_name=X
	# platform_name=X
	device_predicates = db.StringListProperty(default=["platform_name=*"])
	
	# who owns this
	u = db.UserProperty()	
	t = db.DateTimeProperty(auto_now_add=True)
	

# 
# The Ad Group collects actual placement/keyword/category bids 
# and allows users to manage creatives
#
class AdGroup(db.Model):
	campaign = db.ReferenceProperty(Campaign)
	
	name = db.StringProperty()
	bid = db.FloatProperty()
	
	active = db.BooleanProperty(default=True)
	deleted = db.BooleanProperty(default=False)
	
	# all keyword and category bids are tracked here
	# categories use the category:games convention
	# if any of the input keywords match the n-grams here then we 
	# trigger a match
	keywords = db.StringListProperty()
	
	# all placements that are considered for this ad group
	# this is a list of keys corresponding to Site objects
	site_keys = db.ListProperty(db.Key)
	
	def __repr__(self):
		return "AdGroup:'%s'" % self.name

# 
# This is a text creative for house ads
#
IMAGE_PREDICATES = {"300x250": "format=300x250", 
	"320x50": "format=320x50", 
	"300x50": "format=320x50", 
	"728x90": "format=728x90",
	"468x60": "format=468x60"}
class Creative(db.Model):
	ad_group = db.ReferenceProperty(AdGroup)
	
	active = db.BooleanProperty(default=True)
	deleted = db.BooleanProperty(default=False)
	
	ad_type = db.StringProperty(choices=["text", "image"], default="text")
	
	# text ad properties
	headline = db.StringProperty()
	line1 = db.StringProperty()
	line2 = db.StringProperty()
	
	# image properties
	image = db.BlobProperty()
	image_width = db.IntegerProperty()
	image_height = db.IntegerProperty()
	
	# destination URLs
	url = db.StringProperty()
	display_url = db.StringProperty()
	
	# format predicates
	# format=320x50
	# format=*
	format_predicates = db.StringListProperty(default=["format=*"])	
	
	# time of creation
	t = db.DateTimeProperty(auto_now_add=True)
	
	@classmethod
	def get_format_predicates_for_image(c, img):
		fp = IMAGE_PREDICATES.get("%dx%d" % (img.width, img.height))
		return [fp] if fp else None
		
	# calculates the eCPM for this creative, based on 
	# the CPM bid for the ad group or the CPC bid for the ad group and the predicted CTR for this
	# creative
	def e_cpm(self):
		if self.ad_group.campaign.bid_strategy == 'cpc':
			return self.p_ctr() * self.ad_group.bid * 1000
		elif self.ad_group.campaign.bid_strategy == 'cpm':
			return self.ad_group.bid
	
	# predicts a CTR for this ad.  We use 1% for now.
	# TODO: implement this in a better way
	def p_ctr(self):
		return 0.01
			
	def __repr__(self):
		return "Creative:'%s'" % self.headline
		
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
	def sitestats_for_today(c, site):
		return SiteStats.sitestats_for_day(site, datetime.datetime.now().date())
		
	@classmethod
	def today(c):
		return datetime.datetime.now().date()

	@classmethod
	def sitestats_for_day(c, site, d):
		return SiteStats.get_or_insert("%s:%s" % (str(site.key()), str(d)), site=site, date=d)

	@classmethod
	def stats_for_day(c, owner, d):
		return SiteStats.get_or_insert("%s:%s" % (str(owner.key()), str(d)), owner=owner, date=d)
		
	@classmethod
	def stats_for_day_with_qualifier(c, owner, q, d):
		return SiteStats.get_or_insert("%s:%s:%s" % (str(owner.key()), md5.md5(str(q)).hexdigest(), str(d)), owner=owner, date=d)
		
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