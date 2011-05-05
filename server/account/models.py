from django.utils.translation import ugettext_lazy as _

from google.appengine.ext import db
from google.appengine.api import users
from common.ragendja.auth.models import EmailUser


import logging

class User(EmailUser):
    """Default User class that mimics Django's User class."""
    # properties defined in the various abstract super classes
    # last_login = db.DateTimeProperty(verbose_name=_('last login'))
    # date_joined = db.DateTimeProperty(auto_now_add=True,
    #     verbose_name=_('date joined'))
    # is_active = db.BooleanProperty(default=True, verbose_name=_('active'))
    # is_staff = db.BooleanProperty(default=False,
    #     verbose_name=_('staff status'))
    # is_superuser = db.BooleanProperty(default=False,
    #     verbose_name=_('superuser status'))
    # password = db.StringProperty(default=UNUSABLE_PASSWORD,
    #     verbose_name=_('password'))
    # email = db.EmailProperty(required=True, verbose_name=_('e-mail address'))
    # # This can be used to distinguish between banned users and unfinished
    # # registrations
    # is_banned = db.BooleanProperty(default=False,
    #     verbose_name=_('banned status'))    
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    title = db.StringProperty()
    company = db.StringProperty()
    phone = db.PhoneNumberProperty()
    
    user = db.UserProperty()

    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key',None):
            email = kwargs.get('email',None)
            if email:
                key_name = self.get_key_name(email)
        return super(User,self).__init__(parent=parent,key_name=key_name,**kwargs)
        
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
        
    @classmethod
    def kind(cls):
        return "MPUser"
        
    # class Meta:
    #     verbose_name = _('user')
    #     verbose_name_plural = _('users')
            
    def __unicode__(self):
        return self.get_full_name()
        
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
        
    def __eq__(self, other):
        if other:
            return str(self.key()) == str(other.key())
        else:
            return False