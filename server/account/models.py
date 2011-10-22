from django.utils.translation import ugettext_lazy as _

from google.appengine.ext import db
from google.appengine.api import users
from common.ragendja.auth import hybrid_models
from common.constants import ISO_COUNTRIES

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

    rev_share = db.FloatProperty(default=.80)
    price_floor = db.FloatProperty(default=.25) # dollars CPM
    blocklist = db.StringListProperty(indexed=False)

class MarketPlaceConfig(db.Model):
    """ All marketplace related configurations """
    rev_share = db.FloatProperty(default=.90)
    price_floor = db.FloatProperty(default=.25) # dollars CPM
    blocklist = db.StringListProperty(indexed=False)

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
    # Publishers website, this is for MPX
    domain = db.StringProperty()


    active = db.BooleanProperty(default=False)
    status = db.StringProperty()  # Initially storing onboarding status

    adsense_company_name = db.StringProperty()
    adsense_test_mode = db.BooleanProperty(default=False)

    number_shards = db.IntegerProperty(default=4)

    network_config = db.ReferenceProperty(NetworkConfig,
                            collection_name="accounts")
    marketplace_config = db.ReferenceProperty(MarketPlaceConfig,
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

    # have they accepted the marketplace terms of service?
    accepted_mpx_tos = db.BooleanProperty(default=False)

    def is_admin(self):
        return users.is_current_user_admin()

    def __eq__(self, other):
        if other:
            return str(self.key()) == str(other.key())
        else:
            return False


class PaymentInfo(db.Model):
    """
    Customer payment information for RTB

    If 'paypal' is selected for payment preference, we only need their paypal email.

    us_tax_id and ach_routing_number are only required when country == 'US'

    local_tax_id and bank_swift_code are only required when country != 'US'
    """
    country = db.StringProperty(choices=[country[0] for country in ISO_COUNTRIES])
    us_tax_id = db.StringProperty()
    business_name = db.StringProperty()
    local_tax_id = db.StringProperty()
    payment_preference = db.StringProperty(choices=['paypal', 'wire'])
    paypal_email = db.StringProperty()
    beneficiary_name = db.StringProperty()
    bank_name = db.StringProperty()
    bank_address = db.StringProperty()
    account_number = db.StringProperty()
    ach_routing_number = db.StringProperty()
    bank_swift_code = db.StringProperty()
    account = db.ReferenceProperty(Account, collection_name="payment_infos")

    def uses_paypal(self):
        return self.payment_preference == 'paypal'

    def uses_wire(self):
        return self.payment_preference == 'wire'


class PaymentRecord(db.Model):
    account = db.ReferenceProperty(Account, collection_name="payment_records")
    amount = db.StringProperty()
    month = db.IntegerProperty()
    year = db.IntegerProperty()
    status = db.StringProperty()
