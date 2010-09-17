#!/usr/bin/env python

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib
import models

from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class MainHandler(webapp.RequestHandler):
  def get(self):
		start_date = datetime.date.today() - datetime.timedelta(days=14)
		stats = models.SiteStats.gql("where date > :1 order by date desc", start_date).fetch(1000)
		
		# calculate unique active placements (ad slots) and accounts (users)
		# plus accumulate total impression and click counts
		unique_placements = {}
		unique_accounts = {}
		totals = {}
		
		# go and do it
		for s in stats:
			if s.site:
				# add this site stats to the total for the day
				a = totals.get(str(s.date)) or models.SiteStats(date=s.date)
				a.impression_count += s.impression_count
				a.click_count += s.click_count
				totals[str(s.date)] = a
			
				# add a hash key for the site key and account key to calculate uniques
				unique_placements[s.site.key()] = s.site
				unique_accounts[s.site.account.key()] = s.site.account
			
		# organize daily stats
		total_stats = totals.values()
		total_stats.sort(lambda x,y: cmp(x.date,y.date))
		
		# make a graph
		url = "http://chart.apis.google.com/chart?cht=lc&chs=800x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
			 ','.join(map(lambda x: str(x.impression_count), total_stats)), 
			 max(map(lambda x: x.impression_count, total_stats)) * 1.5,
			 max(map(lambda x: x.impression_count, total_stats)) * 1.5,
			 '|'.join(map(lambda x: x.date.strftime("%m/%d"), total_stats)))
			
		# organize placements
		placements = unique_placements.values()
		for p in placements:
			p.stats = models.SiteStats(site=p)
			p.stats.impression_count = sum(map(lambda x: x.impression_count, filter(lambda x: x.site and x.site.key() == p.key(), stats)))
			p.stats.click_count = sum(map(lambda x: x.click_count, filter(lambda x: x.site and x.site.key() == p.key(), stats)))
		placements.sort(lambda x,y: cmp(y.stats.impression_count, x.stats.impression_count))
		
		# thanks
		self.response.out.write(template.render('d.html', {"stats": total_stats, 
			"chart_url": url,
			"impression_count": sum(map(lambda x: x.impression_count, total_stats)),
			"click_count": sum(map(lambda x: x.click_count, total_stats)),
			"ctr": sum(map(lambda x: x.click_count, total_stats)) / sum(map(lambda x: x.impression_count, total_stats)),
			"unique_placements": unique_placements, 
			"unique_accounts": unique_accounts, 
			"placements": placements}))

def main():
  application = webapp.WSGIApplication([('/d', MainHandler)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()
