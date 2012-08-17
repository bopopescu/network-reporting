from common.utils.query_managers import CachedQueryManager, QueryManager

from common.utils.decorators import wraps_first_arg
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

from account.models import Account, User, PaymentRecord, NetworkConfig
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
from common.constants import MAX_OBJECTS

MEMCACHE_KEY_FORMAT = "k:%(user_id)s"

class NetworkConfigQueryManager(CachedQueryManager):
    """Provides an API for getting and putting network config objects."""
    Model = NetworkConfig

    @classmethod
    def get_network_configs_dict_for_account(cls, account):
        return cls.get_entities_for_account(account, NetworkConfig)

    @classmethod
    @wraps_first_arg
    def put(cls, configs):
        db.put(configs)
        affected_account_keys = set([NetworkConfig.account.get_value_for_datastore(config) 
                                     for config in configs])
        cls.memcache_flush_entities_for_account_keys(affected_account_keys, NetworkConfig)

class AccountQueryManager(CachedQueryManager):
    Model = Account

    @classmethod
    def get_current_account(cls,request=None,user=None,cache=False,create=True):
        user = user or request.user
        # if a non logged in user return a None account
        if user.is_anonymous():
            return None
        # try to fetch the account for this user from memcache
        if cache:
            account = memcache.get(str(cls._user_key(user)), namespace=
                    "account")
        else:
            account = None

        # if not in memcache, run the query and put in memcache
        if not account:
            # GQL: get the first account where user in the all_users list
            account = Account.all().filter('all_mpusers =', cls._user_key(user)).get()
            # if no account for this user exists then we need to
            # create the user
            if not account and create:
                account = Account(mpuser=user,
                        all_mpusers=[cls._user_key(user)], status="new",
                        display_new_networks=True)
                account.put()
            if cache:
                memcache.set(str(cls._user_key(user)), account, namespace="account")
        return account

    @classmethod
    def get_account_for_email(cls, email):
        user = UserQueryManager.get_by_email(email)
        return cls.get_current_account(user=user)

    @classmethod
    def update_config_and_put(cls, account, network_config):
        """ Updates the network config and the associated account"""
        network_config.account = account
        NetworkConfigQueryManager.put(network_config)
        account.network_config = network_config
        cls.put_accounts(account)

    @classmethod
    @wraps_first_arg
    def put_accounts(cls, accounts):
        # Delete from cache
        for account in accounts:

            # Delete cached AdUnitContext
            adunits = AdUnitQueryManager.get_adunits(account=account)
            AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

            # Delete cached Accounts for users
            for user_key in account.all_mpusers:
                memcache.delete(str(user_key), namespace="account")

        return db.put(accounts)

    @classmethod
    def _user_key(cls,user):
        return user.key()

    # only to be used for migrations that are manual
    @classmethod
    def migrate(cls,user_email,account_user_email=None,new_account=None):
        user_email = unicode(user_email)
        account_user_email = unicode(account_user_email)
        accounts = Account.all().fetch(1000)
        user = None
        for account in accounts:
            if account.user and account.user.email() == user_email:
                user = account.user
                break

        if not user:
            print "no user"
            user = users.User(email=user_email)
            return

        # get the old account that we don't really need
        old_account = cls.get_current_account(user=user)
        # add the user to the destination account
        if not new_account:
            for account in accounts:
                if account.user.email() == account_user_email:
                    new_account = account
                    break

            if not new_account:
                print "no new account"
                return

        all_users = set(new_account.all_users)
        all_users.add(cls._user_key(user))

        # update the new accounts access list
        new_account.all_users = list(all_users)
        print new_account.all_users
        new_account.put()

        # delete old account as long as the accounts aren't the same
        # if not new_account.key() == old_account.key():
        #     old_account.delete()

    @classmethod
    def get_account_by_key(cls, key):
        return Account.get(key)
        

class UserQueryManager(QueryManager):
    @classmethod
    def get_by_email(cls,email):
        return User.get_by_email(email)

class PaymentRecordQueryManager(QueryManager):
    Model = PaymentRecord

    @classmethod
    def get_payment_records(cls, account=None, deleted=False, limit=MAX_OBJECTS):
        records = PaymentRecord.all()
        if account:
            records = records.filter("account =", account)
        if deleted is not None:
            records = records.filter("deleted =", deleted)

        records = records.filter("scheduled_payment =", False)
        return records.fetch(limit)

    @classmethod
    def get_scheduled_payments(cls, account=None, resolved=False, deleted=False, limit=MAX_OBJECTS):
        records = PaymentRecord.all()
        if account:
            records = records.filter("account =", account)
        records = records.filter("scheduled_payment =", True)
        records = records.filter("resolved =", resolved)
        if deleted is not None:
            records = records.filter("deleted =", deleted)
        return records.fetch(limit)
