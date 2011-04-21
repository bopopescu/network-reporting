from google.appengine.ext import db
from google.appengine.api import users
import logging

#
# The main account
#
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
    
    admob_pub_id = db.StringProperty()
    adsense_pub_id = db.StringProperty()
    adsense_company_name = db.StringProperty()
    adsense_test_mode = db.BooleanProperty(default=False)
    brightroll_pub_id = db.StringProperty()
    greystripe_pub_id = db.StringProperty()
    inmobi_pub_id = db.StringProperty()
    jumptap_pub_id = db.StringProperty()
    millenial_pub_id = db.StringProperty()
    mobfox_pub_id = db.StringProperty()
    
    def is_admin(self):
        return users.is_current_user_admin()
        
    def to_sfdc(self):
        return {'FirstName': (self.first_name or '')[:40],
                'LastName': (self.last_name or '')[:80],
                'Title': (self.title or '')[:80],
                'Company': (self.company or '')[:255], 
                'City': (self.city or '')[:40],
                'State': (self.state or '')[:20],
                'Country': (self.country or '')[:40],
                'Phone': (self.phone or '')[:40],
                'HasOptedOutOfEmail': not self.mailing_list,
                'LeadSource': 'app.mopub.com', 
                'Impressions_Month__c': str(self.traffic) or "Unknown",
                'MoPub_Account_ID__c': str(self.key()),
                'type': 'Lead'}
        
    def __eq__(self, other):
        if other:
            return str(self.key()) == str(other.key())
        else:
            return False