from google.appengine.ext import db
from google.appengine.api import users
import logging

#
# The main account
#
class Account(db.Model):
    user = db.UserProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
        
    company = db.StringProperty(required=True,default="hey")
    phone = db.PhoneNumberProperty()
    traffic = db.IntegerProperty()
    mailing_list = db.BooleanProperty(default=True)
    
    active = db.BooleanProperty(default=False)
    status = db.StringProperty()  # Initially storing onboarding status
    
    admob_pub_id = db.StringProperty()
    adsense_pub_id = db.StringProperty()
    adsense_company_name = db.StringProperty()
    adsense_test_mode = db.BooleanProperty(default=False)
    brightroll_pub_id = db.StringProperty()
    greystripe_pub_id = db.StringProperty()
    inmobi_pub_id = db.StringProperty()
    millenial_pub_id = db.StringProperty()
  
    @classmethod
    def current_account(cls,user=None):
        if not user:
            user = users.get_current_user()
        return Account.get_or_insert(db.Key.from_path("User", user.user_id()).name(), user=user, status="new")

    def is_admin():
        return users.is_current_user_admin()

    def __eq__(self, other):
        if other:
            return str(self.key()) == str(other.key())
        else:
            return False