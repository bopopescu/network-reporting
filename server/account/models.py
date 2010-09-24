from google.appengine.ext import db
from google.appengine.api import users
#
# The main account
#
class Account(db.Model):
	adsense_pub_id = db.StringProperty()
	admob_pub_id = db.StringProperty()
	user = db.UserProperty()
	
	@classmethod
	def current_account(cls):
		u = users.get_current_user()
		return Account.get_or_insert(db.Key.from_path("User", u.user_id()).name(), user=u)

#
# A specific ad placement inside an app
#
