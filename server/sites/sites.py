#!/usr/bin/env python

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib
import models

from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms

class IndexHandler(webapp.RequestHandler):
  def get(self):
		# compute start times; start day before today so incomplete days don't mess up graphs
		today = datetime.date.today() - datetime.timedelta(days=1)
		begin_time = today - datetime.timedelta(days=14)
		days = [today - datetime.timedelta(days=x) for x in range(0, 14)]
	
		# gather aggregate data into each site
		sites = models.Site.gql("where account = :1", models.Account.current_account()).fetch(50)		
		if len(sites) > 0:		
			# organize impressions by days
			day_impressions = {}
			for site in sites:
				stats = models.SiteStats.gql("where site = :1 and date >= :2", site, begin_time).fetch(100)
				site.stats = models.SiteStats()
				site.stats.impression_count = sum(map(lambda x: x.impression_count, stats))
				site.stats.click_count = sum(map(lambda x: x.click_count, stats))
			
				# now aggregate it into days
				for stat in stats:
					day_impressions[stat.date] = (day_impressions.get(stat.date) or 0) + stat.impression_count
	
			# organize the info on a day by day basis across all sites
			series = [day_impressions.get(a,0) for a in days]
			series.reverse()
			url = "http://chart.apis.google.com/chart?cht=lc&chtt=Total+Daily+Impressions&chs=580x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
				 ','.join(map(lambda x: str(x), series)),
				 max(series) * 1.5,
				 max(series) * 1.5,
				 '|'.join(map(lambda x: x.strftime("%m/%d"), days)))
		
			# do a bar graph showing contribution of each site to impression count
			total_impressions_by_site = []
			for site in sites:
				total_impressions_by_site.append({"site": site, "total": site.stats.impression_count})
			total_impressions_by_site.sort(lambda x,y: cmp(y["total"], x["total"]))	
			bar_chart_url = "http://chart.apis.google.com/chart?cht=p&chtt=Contribution+by+Placement&chs=200x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chl=&chdlp=b&chdl=%s" % (
				 ','.join(map(lambda x: str(x["total"]), total_impressions_by_site)),
				 max(map(lambda x: x.stats.impression_count, sites)) * 1.5,
				 max(map(lambda x: x.stats.impression_count, sites)) * 1.5,
				 '|'.join(map(lambda x: x["site"].name, total_impressions_by_site[0:2])))
	
			# stats
			self.response.out.write(template.render('index.html', 
				{'sites': sites, 		
				 'chart_url': url,
				 'bar_chart_url': bar_chart_url,
	 			 'account': models.Account.current_account()}))
		else:
			self.redirect("/sites/create")

class SiteForm(djangoforms.ModelForm):
	class Meta:
		model = models.Site
		fields = ('name', 'url', 'description', 'ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords')

class CreateHandler(webapp.RequestHandler):
  def get(self):
		f = SiteForm()
		self.response.out.write(template.render('new.html', {"f": f}))

  def post(self):
		f = SiteForm(data=self.request.POST)
		site = f.save(commit=False)
		site.account=models.Account.current_account()
		site.put()
		self.redirect('/sites/show?id=%s' % site.key())
	
class UpdateHandler(webapp.RequestHandler):
	def get(self):
		c = models.Site.get(self.request.get("id"))
		f = SiteForm(instance=c)
		self.response.out.write(template.render('edit.html', {"f": f, "site": c}))
		
	def post(self):
		c = models.Site.get(self.request.get('id'))
		f = SiteForm(data=self.request.POST, instance=c)
		if c.account.user == users.get_current_user():
			f.save(commit=False)
			c.put()
		self.redirect('/sites/show?id=%s' % c.key())
	
class GenerateHandler(webapp.RequestHandler):
  def get(self):
	site = models.Site.get(self.request.get('id'))
	self.response.out.write(template.render('code.html', {'site': site}))

class ShowHandler(webapp.RequestHandler):
  def get(self):
	# load the site
	site = models.Site.get(self.request.get('id'))
	if site.account.key() != models.Account.current_account().key():
		self.error(404)
		return
	
	# do all days requested
	today = datetime.date.today() - datetime.timedelta(days=1)
	stats = []
	for x in range(0, 14):
		a = today - datetime.timedelta(days=x)
		m = models.SiteStats.gql("where site = :1 and date = :2", site, a).get()
		if m == None:
			m = models.SiteStats(date=a)
		stats.append(m)

	# chart
	stats.reverse()
	url = "http://chart.apis.google.com/chart?cht=lc&chs=800x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
		 ','.join(map(lambda x: str(x.impression_count), stats)), 
		 max(map(lambda x: x.impression_count, stats)) * 1.5,
		 max(map(lambda x: x.impression_count, stats)) * 1.5,
		 '|'.join(map(lambda x: x.date.strftime("%m/%d"), stats)))
		
	# totals
	impression_count = sum(map(lambda x: x.impression_count, stats))
	click_count = sum(map(lambda x: x.click_count, stats))
	ctr = float(click_count) / float(impression_count) if impression_count > 0 else 0
	
	# write response
	self.response.out.write(template.render('show.html', {'site':site, 
		'impression_count': impression_count, 'click_count': click_count, 'ctr': ctr,
		'account':models.Account.current_account(), 
		'chart_url': url,
		'stats':stats}))

def main():
  application = webapp.WSGIApplication([('/sites', IndexHandler), 
										('/sites/create', CreateHandler),
										('/sites/update', UpdateHandler),
										('/sites/generate', GenerateHandler),
										('/sites/show', ShowHandler)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()

