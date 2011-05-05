import logging

from common.utils.query_managers import CachedQueryManager, QueryManager

from common.utils.decorators import wraps_first_arg
from advertiser.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

from account.models import Account, User
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

MEMCACHE_KEY_FORMAT = "k:%(user_id)s"

class AccountQueryManager(CachedQueryManager):
    Model = Account

    @classmethod
    def get_current_account(cls,user=None):
        if not user:
            user = users.get_current_user()
        # try to fetch the account for this user from memcache      
        account = memcache.get(str(cls._user_key(user)), namespace="account")    
        
        # if not in memcache, run the query and put in memcache
        if not account:
            logging.warning("account not in cache, user: %s" % cls._user_key(user))
            # GQL: get the first account where user in the all_users list
            account = Account.all().filter('all_users =', cls._user_key(user)).get()
            # if no account for this user exists then we need to 
            # create the user
            if not account:
                logging.warning("account needs to be created")
                account = Account(user=user, all_users=[cls._user_key(user)], status="new")    
                account.put()
            memcache.set(str(cls._user_key(user)), account, namespace="account")
        logging.warning("account: %s"%account.key())    
        return account

    @classmethod
    @wraps_first_arg
    def put_accounts(cls, accounts):
        # Delete from cache
        for account in accounts:

            # Delete cached AdUnitContext
            adunits = AdUnitQueryManager.get_adunits(account=account)
            AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
            
            # Delete cached Accounts for users
            for user_key in account.all_users:
                memcache.delete(str(user_key), namespace="account")

        return db.put(accounts)    
    
    @classmethod    
    def _user_key(cls,user):
        return db.Key.from_path("User", user.user_id())     


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

class UserQueryManager(QueryManager):
    
    @classmethod
    def get_by_email(cls,email):
        return cls.get_by_email(email)       