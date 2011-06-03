from django.utils.translation import ugettext_lazy as _

from google.appengine.ext import db
from google.appengine.api import users
from common.ragendja.auth import hybrid_models

import logging

class User(hybrid_models.User):
    title = db.StringProperty()
    company = db.StringProperty()
    phone = db.PhoneNumberProperty()
    country = db.StringProperty()
    state = db.StringProperty()
    city = db.StringProperty()

    mailing_list = db.BooleanProperty(default=False)

    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key',None):
            email = kwargs.get('email',None)
            if email:
                key_name = self.get_key_name(email)
        return super(User,self).__init__(parent=parent,key_name=key_name,**kwargs)
    
    @property
    def id(self):
        return str(self.key())    
        
    @property
    def is_admin(self):
        return self.is_staff    
                
    @classmethod
    def get_key_name(cls, email):
        return 'k:'+email.lower().\
                        replace('@','_at_').\
                        replace('.','_dot_').\
                        replace('+','_plus_')
        
    @classmethod    
    def get_key(cls,email):
        return db.Key.from_path(cls.kind(),cls.get_key_name(email))

    @classmethod
    def get_by_email(cls, email):
        return cls.get(cls.get_key(email))
        
    def __unicode__(self):
        return "User: "+self.email
        
    def __repr__(self):
        return unicode(self)    
#
# The main account
#
class NetworkConfig(db.Model):
    """ The set of ids for all the different networks """
    admob_pub_id = db.StringProperty()
    adsense_pub_id = db.StringProperty()
    brightroll_pub_id = db.StringProperty()
    chartboost_pub_id = db.StringProperty()
    ejam_pub_id = db.StringProperty()
    greystripe_pub_id = db.StringProperty()
    inmobi_pub_id = db.StringProperty()
    jumptap_pub_id = db.StringProperty()
    millennial_pub_id = db.StringProperty()
    mobfox_pub_id = db.StringProperty()

class Account(db.Model):
    user = db.UserProperty() # admin user for this account
    all_users = db.ListProperty(db.Key)    
    
    mpuser = db.ReferenceProperty(User)
    all_mpusers = db.ListProperty(db.Key)
    date_added = db.DateTimeProperty(auto_now_add=True)

    first_name = db.StringProperty()
    last_name = db.StringProperty()
    title = db.StringProperty()
    company = db.StringProperty()
    phone = db.PhoneNumberProperty()
    country = db.StringProperty()
    traffic = db.FloatProperty()

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
    chartboost_pub_id = db.StringProperty()
    ejam_pud_id = db.StringProperty()
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