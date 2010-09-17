from google.appengine.ext import db
from google.appengine.api import users
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
