from django.conf import settings
from google.appengine.ext import db
from google.appengine.api import users

from common.ragendja.auth import hybrid_models
from common.constants import ISO_COUNTRIES
from simple_models import SimpleNetworkConfig, SimpleAccount


class User(hybrid_models.User):
    title = db.StringProperty()
    company = db.StringProperty()
    phone = db.PhoneNumberProperty()
    address1 = db.StringProperty()
    address2 = db.StringProperty()
    city = db.StringProperty()
    state = db.StringProperty()
    zipcode = db.StringProperty()
    country = db.StringProperty()

    mailing_list = db.BooleanProperty(default=False)

    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key', None):
            email = kwargs.get('email', None)
            if email:
                key_name = self.get_key_name(email)
        return super(User, self).__init__(parent=parent, key_name=key_name, **kwargs)

    @property
    def id(self):
        return str(self.key())

    @property
    def is_admin(self):
        return self.is_staff

    @classmethod
    def get_key_name(cls, email):
        return 'k:' + email.lower().\
                        replace('@', '_at_').\
                        replace('.', '_dot_').\
                        replace('+', '_plus_')

    @classmethod
    def get_key(cls, email):
        """
        Deprecated
        """
        return db.Key.from_path(cls.kind(), cls.get_key_name(email))

    @classmethod
    def get_by_email(cls, email):
        """Gets the most recently logged in user with a particular email address"""
        email = email.lower()
        possible_users = cls.all().filter('email =', email).fetch(100)
        sorted_users = sorted(possible_users, key=lambda x: x.last_login, reverse=True)
        if sorted_users:
            return sorted_users[0]
        else:
            return None

    def __unicode__(self):
        return "User: " + self.email

    def __repr__(self):
        return unicode(self)


#
# The main account
#
DEFAULT_CATEGORIES = ["IAB25"]
LOW_CATEGORIES = ["IAB25"]
MODERATE_CATEGORIES = ["IAB25",
                       "IAB7-39",
                       "IAB8-5",
                       "IAB8-18",
                       "IAB9-9",
                       "IAB14-1"]
STRICT_CATEGORIES = ["IAB25",
                     "IAB7-39",
                     "IAB8-5",
                     "IAB8-18",
                     "IAB9-9",
                     "IAB14-1",
                     "IAB6-7",
                     "IAB7-3",
                     "IAB7-28",
                     "IAB7-30",
                     "IAB14-2",
                     "IAB14-3"]
DEFAULT_ATTRIBUTES = [10, 14]
LOW_ATTRIBUTES = \
MODERATE_ATTRIBUTES = \
STRICT_ATTRIBUTES = [9, 10, 14]


class NetworkConfig(db.Model):
    """ The set of ids for all the different networks """
    # iad_pub_id is stored in the app url. Take a look at publisher's query
    # managers for App for more information.
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

    # marketplace related
    rev_share = db.FloatProperty(default=.80)
    price_floor = db.FloatProperty(default=.25)  # dollars CPM
    blocklist = db.StringListProperty(indexed=False)
    category_blocklist = db.StringListProperty(indexed=False,
                                    default=MODERATE_CATEGORIES)
    attribute_blocklist = db.ListProperty(int,
                                          indexed=False,
                                          default=MODERATE_ATTRIBUTES)
    blind = db.BooleanProperty(default=False)

    def simplify(self):
        return SimpleNetworkConfig(admob_pub_id = self.admob_pub_id,
                                   adsense_pub_id = self.adsense_pub_id,
                                   brightroll_pub_id = self.brightroll_pub_id,
                                   chartboost_pub_id = self.chartboost_pub_id,
                                   ejam_pub_id = self.ejam_pub_id,
                                   greystripe_pub_id = self.greystripe_pub_id,
                                   inmobi_pub_id = self.inmobi_pub_id,
                                   jumptap_pub_id = self.jumptap_pub_id,
                                   millennial_pub_id = self.millennial_pub_id,
                                   mobfox_pub_id = self.mobfox_pub_id,
                                   rev_share = self.rev_share,
                                   price_floor = self.price_floor,
                                   blocklist = self.blocklist,
                                   blind = self.blind,
                                   category_blocklist = self.category_blocklist,
                                   attribute_blocklist = self.attribute_blocklist,
                                   )
    @property
    def filter_level(self):
        if sorted(self.category_blocklist) == sorted(DEFAULT_CATEGORIES) and \
           sorted(self.attribute_blocklist) == sorted(DEFAULT_ATTRIBUTES):
            return "none"
        elif sorted(self.category_blocklist) == sorted(LOW_CATEGORIES) and \
             sorted(self.attribute_blocklist) == sorted(LOW_ATTRIBUTES):
            return "low"
        elif sorted(self.category_blocklist) == sorted(MODERATE_CATEGORIES) and \
             sorted(self.attribute_blocklist) == sorted(MODERATE_ATTRIBUTES):
            return "moderate"
        elif sorted(self.category_blocklist) == sorted(STRICT_CATEGORIES) and \
             sorted(self.attribute_blocklist) == sorted(STRICT_ATTRIBUTES):
            return "strict"
        else:
            return "custom"

    def set_strict_filter(self):
        self.attribute_blocklist = STRICT_ATTRIBUTES
        self.category_blocklist = STRICT_CATEGORIES
        self.put()

    def set_moderate_filter(self):
        self.attribute_blocklist = MODERATE_ATTRIBUTES
        self.category_blocklist = MODERATE_CATEGORIES
        self.put()

    def set_low_filter(self):
        self.attribute_blocklist = LOW_ATTRIBUTES
        self.category_blocklist = LOW_CATEGORIES
        self.put()

    def set_no_filter(self):
        self.attribute_blocklist = DEFAULT_ATTRIBUTES
        self.category_blocklist = DEFAULT_CATEGORIES
        self.put()


class MarketPlaceConfig(db.Model):
    """ All marketplace related configurations """
    rev_share = db.FloatProperty(default=.90)
    price_floor = db.FloatProperty(default=.25)  # dollars CPM
    blocklist = db.StringListProperty(indexed=False)


class Account(db.Model):
    user = db.UserProperty()  # admin user for this account
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

    # use MongoDB for realtime stats
    # ex: Outblaze and Mobipeak have too many apps for GAE realtime stats to
    # handle
    use_mongodb_stats = db.BooleanProperty(default=False if settings.DEBUG else True)

    # use only mongo, not datastore for storing real time stats
    use_only_mongo = db.BooleanProperty(default=False)

    # AdNetworkReports account level settings
    ad_network_email = db.BooleanProperty(default=False)
    ad_network_recipients = db.StringListProperty()

    # account sees new networks page
    display_new_networks = db.BooleanProperty(default=False)
    display_networks_message = db.BooleanProperty(default=False)

    # use only mongo to display realtime stats in UI
    display_mongo = db.BooleanProperty(default=False if settings.DEBUG else True)

    def simplify(self):
        return SimpleAccount(key = str(self.key()),
                             company = self.company,
                             domain = self.domain,
                             network_config = self.network_config,
                             adsense_company_name = self.adsense_company_name,
                             adsense_test_mode = self.adsense_test_mode,
                             )

    @property
    def emails(self):
        """Return a list of emails for this account."""
        return [db.get(user).email for user in self.all_mpusers]

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

    If 'paypal' is selected for payment preference, we only need their paypal
    email.

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
    amount = db.FloatProperty(default=float(0))
    status = db.StringProperty()
    date_executed = db.DateTimeProperty()
    period_start = db.DateProperty()
    period_end = db.DateProperty()
    scheduled_payment = db.BooleanProperty(default=False)  # Whether this is a scheduled payment of actual payment
    resolved = db.BooleanProperty(default=False)  # For scheduled payment, resolved means it has been paid
    created = db.DateTimeProperty(auto_now_add=True)

    deleted = db.BooleanProperty(default=False)
