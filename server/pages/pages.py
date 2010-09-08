#!/usr/bin/env python

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib, urllib, models, random, traceback

from urllib import urlencode
from django.utils import simplejson

from google.appengine.api import users, memcache, images
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.ext.db import djangoforms

from oauth.twitter_oauth_handler import OAuthClient

class IndexHandler(webapp.RequestHandler):
  def get(self, id):
		p = models.LandingPage.get(id)
		b = models.Bid.get(self.request.get("bid")) if self.request.get("bid") else None
		c = models.Creative.get(self.request.get("creative")) if self.request.get("creative") else None
		
		# make sure the page is up to date
		p.refresh()

		self.response.out.write(template.render('index.html', {'p':p, 'b': b, 'c': c}))
		
class LogoHandler(webapp.RequestHandler):
  def get(self, id):
		p = models.LandingPage.get(id)
		if p.logo_image:
			self.response.headers['Content-Type'] = "image/png"
			self.response.out.write(p.logo_image)
		else:
			self.error(404)
						
class TrackImpression(webapp.RequestHandler):
	def post(self, id):
		p = models.LandingPage.get(id)
		
		# get the originating search terms
		b = models.Bid.get(self.request.get("bid")) if self.request.get("bid") else None
		c = models.Creative.get(self.request.get("creative")) if self.request.get("creative") else None
		
		# generate a cookie and drop it on the user's machine
		cookie = models.LandingPageCookie(landing_page=p, bid=b, creative=c, remote_addr=self.request.remote_addr)
		cookie.put()
				
		# increment stuff
		def txn(x):
			if x:
				x.impression_count += 1
				x.put()
		db.run_in_transaction(txn, p.campaign)
		db.run_in_transaction(txn, p)
		db.run_in_transaction(txn, b)
		db.run_in_transaction(txn, c)
		
		# drop cookie
		self.response.headers.add_header("Set-Cookie", "landing_page=%s; expires=Sun, 17-Jan-2038 23:59:59 GMT; path=/" % cookie.key())
		self.response.out.write("OK")

class ClickHandler(webapp.RequestHandler):	
	def post(self, id):
		p = models.LandingPage.get(id)

		# get the originating search terms
		b = models.Bid.get(self.request.get("bid")) if self.request.get("bid") else None
		c = models.Creative.get(self.request.get("creative")) if self.request.get("creative") else None

		# track this page view back to the campaign and the landing page (unless a test view)
		if not self.request.get("test"):
			def txn(x):
				if x:
					x.click_count += 1
					x.put()
			db.run_in_transaction(txn, p.campaign)
			db.run_in_transaction(txn, p)
			db.run_in_transaction(txn, b)
			db.run_in_transaction(txn, c)
			
		# simulate it here
		if OAuthClient('twitter', self).get_cookie():
			self.redirect("/pages/f/%s?retweet=%s" % (p.key(), self.request.get("retweet")))
		else:
			# make sure the cookie is valid
			cookie = models.LandingPageCookie.get(self.request.cookies.get('landing_page'))
			cookie.retweet = self.request.get("retweet") != ""
			cookie.put()
			
			# redirect to twitter
			self.redirect("/oauth/twitter/login")

class CallbackHandler(webapp.RequestHandler):
	def get(self):
		key = self.request.cookies.get('landing_page') 
		if key:
			cookie = models.LandingPageCookie.get(key)
			if cookie:
				self.redirect("/pages/f/%s?retweet=%s" % (cookie.landing_page.key(), self.request.get("retweet")))
		
class FollowHandler(webapp.RequestHandler):

	BITLY_LOGIN = "gethighnote"
	BITLY_APIKEY = "R_6ab7663bd614f5dc813b1f0a1a3da625"
			
	def shorten_url(self, url):
		json = fetch("http://api.bit.ly/shorten?version=2.0.1&%s" % 
			urllib.urlencode([("longUrl", url), ("login", self.BITLY_LOGIN), ("apiKey", self.BITLY_APIKEY)])).content
		return simplejson.loads(json)["results"][url]["shortUrl"]
			
	def get(self, id):
		p = models.LandingPage.get(id)
		retweet = bool(self.request.get("retweet"))
		
		# do the key operations
		try:
			# who are we following?
			client = OAuthClient("twitter", self)
			account_info = client.get("/account/verify_credentials")

			# create following relationship
			try:
				client.post("http://twitter.com/friendships/create/%s.json" % p.campaign.asset.screen_name)
			except:
				logging.debug("Failed to follow %s, continuing..." % p.campaign.asset.screen_name)
				logging.debug(traceback.format_exc())

			# retweet
			if True: #retweet:
				client.post("http://twitter.com/statuses/update.json", 
					status="Just started following %s (%s). Check it out %s" % (p.campaign.asset.status().get("name"), p.campaign.asset.screen_name, self.shorten_url("http://www.highnotenetworks.com/pages/%s" % p.key())))

			# record the conversion
			conversion = models.Conversion(landing_page_cookie=models.LandingPageCookie.get(self.request.cookies.get('landing_page')), 
				asset=models.RTAsset.get_asset(account_info["screen_name"]),
				campaign=p.campaign,
				retweet=retweet,
				remote_addr=self.request.remote_addr)
			conversion.put()
		except:
			logging.error(traceback.format_exc())
			
		# get the originating search terms
		b = models.Bid.get(self.request.get("bid")) if self.request.get("bid") else None
		c = models.Creative.get(self.request.get("creative")) if self.request.get("creative") else None

		# track this page view back to the campaign and the landing page (unless a test view)
		if not self.request.get("test"):
			def txn(x):
				if x:
					x.follow_count += 1
					x.put()
			db.run_in_transaction(txn, p.campaign)
			db.run_in_transaction(txn, p)
			db.run_in_transaction(txn, b)
			db.run_in_transaction(txn, c)

		# render a thank you page
		r = p.redirect_url or ("http://www.%s.com/%s" % (p.campaign.asset.service_name, p.campaign.asset.screen_name))
		self.response.out.write(template.render("index.html", {"r": r, "p": p}))


class LandingPageForm(djangoforms.ModelForm):
	class Meta:
		model = models.LandingPage
		fields = ('headline', 'line1', 'line2', 'call_to_action', 
			'show_background', 'show_last_tweet', 'show_followers', 'show_embed', 'youtube_id', 'redirect_url')
		
class CreatePageHandler(webapp.RequestHandler):
	def get(self):
		f = LandingPageForm()
		c = models.Campaign.get(self.request.get("id"))
		self.response.out.write(template.render("new.html", {"f": f, "c": c}))
		
	def post(self):
		f = LandingPageForm(data=self.request.POST)
		p = f.save(commit=False)
		p.logo_image = images.resize(self.request.get("logo"), 800, 200) if self.request.get("logo") else None
		p.campaign=models.Campaign.get(self.request.get("id"))
		p.put()
		self.redirect("/campaigns/show/%s" % p.campaign.key())
		
class RemovePageHandler(webapp.RequestHandler):
	def post(self):
		p = models.LandingPage.get(self.request.get("id"))
		p.delete()
		self.redirect("/campaigns/show/%s" % p.campaign.key())

class ViewBidHandler(webapp.RequestHandler):
	def get(self, id):
		b = models.Bid.get(id)
		p = random.choice(models.LandingPage.gql("where campaign=:1", b.campaign).fetch(10))
		self.redirect("/pages/%s?bid=%s" % (p.key(), b.key()))

def main():
  application = webapp.WSGIApplication([('/pages/create', CreatePageHandler), 	
		('/pages/remove', RemovePageHandler),
		('/pages/r/([-\w]+)', ViewBidHandler),
		('/pages/imp/([-\w]+)', TrackImpression),		# called by javascript to register an impression by something other than a bot
		('/pages/clk/([-\w]+)', ClickHandler),			# handles sending the user through an OAUTH process
		('/pages/callback', CallbackHandler),				# handles the OAUTH completion, redirects to the right /f URL
		('/pages/f/([-\w]+)', FollowHandler),				# handles the OAUTH completion, does the follow, and completes w/ a redirect
		('/pages/logo/([-\w]+)', LogoHandler),
		('/pages/([-\w]+)', IndexHandler)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()

