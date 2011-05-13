from google.appengine.ext import db
from google.appengine.api import users
import logging



class NetworkConfig(db.Model):
    """ The set of ids for all the different networks """
    admob_pub_id = db.StringProperty()
    adsense_pub_id = db.StringProperty()
    brightroll_pub_id = db.StringProperty()
    greystripe_pub_id = db.StringProperty()
    inmobi_pub_id = db.StringProperty()
    jumptap_pub_id = db.StringProperty()
    millennial_pub_id = db.StringProperty()
    mobfox_pub_id = db.StringProperty()


class Account(db.Model):
    user = db.UserProperty() # admin user for this account
    date_added = db.DateTimeProperty(auto_now_add=True)
    all_users = db.ListProperty(db.Key)    
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    title = db.StringProperty()
    company = db.StringProperty()
    phone = db.PhoneNumberProperty()
    city = db.StringProperty()
    state = db.StringProperty()
    country = db.StringProperty()
    traffic = db.FloatProperty()
    mailing_list = db.BooleanProperty(default=False)
    
    active = db.BooleanProperty(default=False)
    status = db.StringProperty()  # Initially storing onboarding status
    
    adsense_company_name = db.StringProperty()
    adsense_test_mode = db.BooleanProperty(default=False)
    
    network_config = db.ReferenceProperty(NetworkConfig,
                            collection_name="accounts")
    
    # Still here for transfering
    admob_pub_id = db.StringProperty()
    adsense_pub_id = db.StringProperty()
    brightroll_pub_id = db.StringProperty()
    greystripe_pub_id = db.StringProperty()
    inmobi_pub_id = db.StringProperty()
    jumptap_pub_id = db.StringProperty()
    millennial_pub_id = db.StringProperty()
    mobfox_pub_id = db.StringProperty()
    
    def is_admin(self):
        return users.is_current_user_admin()
        
    def __eq__(self, other):
        if other:
            return str(self.key()) == str(other.key())
        else:
            return False