#!/usr/bin/env python

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib, models

from django.utils import simplejson

from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class SplashHandler(webapp.RequestHandler):
	def get(self):
		self.response.out.write(template.render('splash.html', {}))
		# self.redirect("/main")

class MainHandler(webapp.RequestHandler):
  def get(self):
		self.response.out.write(template.render('index.html', {}))

class AboutHandler(webapp.RequestHandler):
  def get(self):
		self.response.out.write(template.render('about.html', {}))
	
class AccountHandler(webapp.RequestHandler):
	def get(self):
		self.response.out.write(template.render('account.html', {'account': models.Account.current_account()}))
		
	def post(self):
		a = models.Account.current_account()
		a.adsense_pub_id = self.request.get("adsense_pub_id")
		a.default_keywords = self.request.get("default_keywords")
		a.put()
		self.redirect("/sites")

def main():
  application = webapp.WSGIApplication([('/', SplashHandler), 
										('/main', MainHandler),
										('/account', AccountHandler),
										('/about', AboutHandler)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()
