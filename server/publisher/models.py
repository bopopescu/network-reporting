from google.appengine.ext import db
from google.appengine.api import users

from account.models import Account

# 
# A mobile app, which can have multiple Sites on which ads can be displayed
#
class App(db.Model):
	account = db.ReferenceProperty(Account)

	name = db.StringProperty()
	app_type = db.StringProperty(required=True, default="iphone", choices=["iphone", "android", "ipad"])
	description = db.TextProperty()
	url = db.StringProperty()

	t = db.DateTimeProperty(auto_now_add=True)

class Site(db.Model):
	app_key = db.ReferenceProperty(App)
	account = db.ReferenceProperty(Account)
	
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
