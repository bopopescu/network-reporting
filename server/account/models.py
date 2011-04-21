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
    company = db.StringProperty()
    phone = db.PhoneNumberProperty()
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
        return {'Company': self.name, 
                'FirstName': "A", 'LastName': "Developer",
                'LeadSource': 'AppStoreCrawl', 
                'Number_of_Apps__c': len(self.apps),
                'Apps__c': "\n".join(["%s (#%d in %s)" % (a.get("title"), a.get("rank"), a.get("category")) for a in self.apps]),
                'iTunesURL__c': max([a.get("url") for a in self.apps]),
                'Top_Rank__c': min(a.get('rank') for a in self.apps),
                'Primary_Category__c': max(set(categories), key=categories.count),
                'iTunes_Artist_Name__c': max([a.get('artist') for a in self.apps]),
                'HtmlSummary__c': "<hr/>".join([a.get('summary') for a in self.apps]),
                'Description': '',
                'type': 'Lead'}
        
    def __eq__(self, other):
        if other:
            return str(self.key()) == str(other.key())
        else:
            return False