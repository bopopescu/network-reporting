#!/usr/bin/env python

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib
import models
import random

from urllib import urlencode

from google.appengine.api import users, memcache, images
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.ext.db import djangoforms
		
class CampaignForm(djangoforms.ModelForm):
	class Meta:
		model = models.Campaign
		fields = ('name', 'description', 'budget', 'bid_strategy', 'geo_predicates', 'device_predicates')

class IndexHandler(webapp.RequestHandler):
  def get(self):
		campaigns = models.Campaign.gql("where u = :1 and deleted = :2", users.get_current_user(), False).fetch(10)
		for c in campaigns:
			c.stats = models.SiteStats.stats_for_day(c, models.SiteStats.today())
		self.response.out.write(template.render('index.html', {'campaigns':campaigns, 'user':users.get_current_user()}))

class CreateHandler(webapp.RequestHandler):
	def get(self):
		f = CampaignForm()
		self.response.out.write(template.render('new.html', {"f": f}))

	def post(self):
		f = CampaignForm(data=self.request.POST)
		campaign = f.save(commit=False)
		campaign.u = users.get_current_user() 
		campaign.put()
		self.redirect('/campaigns/show/%s' % campaign.key())

class EditHandler(webapp.RequestHandler):
	def get(self):
		c = models.Campaign.get(self.request.get("id"))
		f = CampaignForm(instance=c)
		self.response.out.write(template.render('edit.html', {"f": f, "campaign": c}))
		
	def post(self):
		c = models.Campaign.get(self.request.get('id'))
		f = CampaignForm(data=self.request.POST, instance=c)
		if c.u == users.get_current_user():
			f.save(commit=False)
			c.put()
		self.redirect('/campaigns/show/%s' % c.key())

class PauseHandler(webapp.RequestHandler):
  def post(self):
		c = models.Campaign.get(self.request.get('id'))
		if c != None and c.u == users.get_current_user():
			c.active = not c.active
			c.deleted = False
			c.put()
			self.redirect('/campaigns/show/%s' % c.key())

class DeleteHandler(webapp.RequestHandler):
  def post(self):
		c = models.Campaign.get(self.request.get('id'))
		if c != None and c.u == users.get_current_user():
			c.active = False
			c.deleted = True
			c.put()
			self.redirect('/campaigns')

class ShowHandler(webapp.RequestHandler):
  def get(self, id):
		# load the campaign
		campaign = models.Campaign.get(id)
		campaign.stats = models.SiteStats.stats_for_day(campaign, models.SiteStats.today())
		
		# load the adgroups
		bids = models.AdGroup.gql("where campaign=:1 and deleted = :2", campaign, False).fetch(50)
		for b in bids:
			b.stats = models.SiteStats.stats_for_day(b, models.SiteStats.today())
	
		# write response
		self.response.out.write(template.render('show.html', 
			{'campaign':campaign, 
			 'bids': bids,
			 'sites': models.Site.gql('where account=:1', models.Account.current_account()),
			 'user':users.get_current_user()}))
			
#
# Ad Group stuff
#
class AdGroupForm(djangoforms.ModelForm):
	class Meta:
		model = models.AdGroup
		fields = ('name', 'bid')

class AddBidHandler(webapp.RequestHandler):
  def post(self):
		c = models.Campaign.get(self.request.get('id'))
		adgroup = models.AdGroup(campaign=c,
			name=self.request.get('name'),
			bid=float(self.request.get('bid')),
			keywords=filter(lambda k: len(k) > 0, self.request.get('keywords').lower().split('\n')),
			site_keys=map(lambda x: db.Key(x), self.request.get_all('sites')))
		adgroup.put()
		self.redirect('/campaigns/show/%s' % c.key())
		
class EditBidHandler(webapp.RequestHandler):
	def get(self):
		a = models.AdGroup.get(self.request.get("id"))
		f = AdGroupForm(instance=a)
		params = {"f": f, 
		 'sites': models.Site.gql('where account=:1', models.Account.current_account()).fetch(100),
		"a": a, 
		"campaign": a.campaign}
		for s in params['sites']:
			s.checked = s.key() in a.site_keys
		
		logging.info(params)	
		self.response.out.write(template.render('adgroup_edit.html', params))
		
	def post(self):
		a = models.AdGroup.get(self.request.get("id"))
		f = AdGroupForm(data=self.request.POST, instance=a)
		if a.campaign.u == users.get_current_user():
			logging.info(f)
			a.site_keys = map(lambda x:db.Key(x), self.request.get_all("site_keys"))
			a.keywords = filter(lambda k: len(k) > 0, self.request.get('keywords').lower().split('\n'))
			f.save(commit=False)
			a.put()
		self.redirect('/campaigns/adgroup/%s' % a.key())

class RemoveBidHandler(webapp.RequestHandler):
  def post(self):
		for id in self.request.get_all('id') or []:
			b = models.AdGroup.get(id)
			logging.info(b)
			if b != None and b.campaign.u == users.get_current_user():
				b.deleted = True
				b.put()
		self.redirect('/campaigns/show/%s' % b.campaign.key())

class PauseBidHandler(webapp.RequestHandler):
  def post(self):
		for id in self.request.get_all('id'):
			b = models.AdGroup.get(id)
			logging.info(b)
			if b != None and b.campaign.u == users.get_current_user():
				b.active = not b.active
				b.deleted = False
				b.put()
		self.redirect('/campaigns/adgroup/%s' % b.key())
		
class ShowAdGroupHandler(webapp.RequestHandler):
	def get(self, id):
		adgroup = models.AdGroup.get(id)
		creatives = models.Creative.gql('where ad_group = :1 and deleted = :2', adgroup, False).fetch(50)
		for c in creatives:
			c.stats = models.SiteStats.stats_for_day(c, models.SiteStats.today())
		sites = map(lambda x: models.Site.get(x), adgroup.site_keys)
		for s in sites:
			s.stats = models.SiteStats.stats_for_day_with_qualifier(adgroup, s.key(), models.SiteStats.today())
		keywords = map(lambda k: {"keyword": k, "stats": models.SiteStats.stats_for_day_with_qualifier(adgroup, k, models.SiteStats.today())}, adgroup.keywords)
		
		self.response.out.write(template.render('adgroup.html', 
			{'campaign': adgroup.campaign,
			 'adgroup': adgroup, 
			 'sites': sites,
			 'keywords': keywords, 
			 'creatives': creatives}))

#
# Creative management
#

class AddCreativeHandler(webapp.RequestHandler):
  def post(self):
		ad_group = models.AdGroup.get(self.request.get('id'))
		if self.request.get("headline"):
			creative = models.Creative(ad_group=ad_group,
				headline=self.request.get('headline'),
				line1=self.request.get('line1'),
				line2=self.request.get('line2'),
				url=self.request.get('url'),
				display_url=self.request.get('display_url'))
			creative.put()
		elif self.request.get("image"):
			img = images.Image(self.request.get("image"))
			fp = models.Creative.get_format_predicates_for_image(img)
			if fp is not None:
				creative = models.Creative(ad_group=ad_group,
					ad_type="image",
					format_predicates=fp,
					url=self.request.get('url'),
					image=self.request.get("image"),
					image_width=img.width,
					image_height=img.height)
				creative.put()
		self.redirect('/campaigns/adgroup/%s' % ad_group.key())

class RemoveCreativeHandler(webapp.RequestHandler):
  def post(self):
		c = models.Creative.get(self.request.get('id'))
		if c != None and c.ad_group.campaign.u == users.get_current_user():
			c.deleted = True
			c.put()
			self.redirect('/campaigns/adgroup/%s' % c.ad_group.key())
			
class DisplayCreativeHandler(webapp.RequestHandler):
	def get(self, id):
		c = models.Creative.get(id)
		if c and c.ad_type == "image" and c.image:
			self.response.headers["Content-Type"] = "image/png"			
			self.response.out.write(c.image)				

def main():
  application = webapp.WSGIApplication([('/campaigns', IndexHandler), 
										('/campaigns/create', CreateHandler),
										('/campaigns/edit', EditHandler),
										('/campaigns/delete', DeleteHandler),
										('/campaigns/pause', PauseHandler),
										('/campaigns/show/([-\w\.]+)', ShowHandler),
										('/campaigns/creative/create', AddCreativeHandler),
										('/campaigns/creative/remove', RemoveCreativeHandler),
										('/campaigns/creative/image/([-\w\.]+)', DisplayCreativeHandler),
										('/campaigns/bid/create', AddBidHandler),
										('/campaigns/adgroup/edit', EditBidHandler),
										('/campaigns/bid/pause', PauseBidHandler),
										('/campaigns/bid/remove', RemoveBidHandler),
										('/campaigns/adgroup/([-\w\.]+)', ShowAdGroupHandler)
										], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()

