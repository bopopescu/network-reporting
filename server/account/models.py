from google.appengine.ext import db
from google.appengine.api import users
import logging

#
# The main account
#
class Account(db.Model):
  adsense_pub_id = db.StringProperty()
  adsense_company_name = db.StringProperty()
  adsense_test_mode = db.BooleanProperty()
  admob_pub_id = db.StringProperty()
  user = db.UserProperty()
  date_added = db.DateTimeProperty(auto_now_add=True)
  active = db.BooleanProperty(default=False)
  
  @classmethod
  def current_account(cls,user=None):
    if not user:
      user = users.get_current_user()
    return Account.get_or_insert(db.Key.from_path("User", user.user_id()).name(), user=user)

  def is_admin():
    return users.is_current_user_admin()
    
  def __eq__(self, other):
    if other:
      return str(self.key()) == str(other.key())
    else:
      return False