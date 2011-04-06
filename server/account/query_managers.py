import logging

from common.utils.cachedquerymanager import CachedQueryManager

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

from account.models import Account

MEMCACHE_KEY_FORMAT = "k:%(user)s"

class AccountQueryManager(CachedQueryManager):
    Model = Account
    def get_by_key_name(self,name):
        return self.Model.get_by_key_name(name)
    def get_current_account(self,user=None):
        if not user:
            user = users.get_current_user()
        # try to fetch the account for this user from memcache    
        memcache_key = MEMCACHE_KEY_FORMAT%dict(user=user)    
        account = memcache.get(memcache_key)    
        # if not in memcache, run the query and put in memcache
        if not account:
            logging.warning("account not in cache, user: %s"%self._user_key(user))
            # GQL: get the first account where user in the all_users list
            account = Account.all().filter('all_users =',self._user_key(user)).get()
            # if no account for this user exists then we need to 
            # create the user
            if not account:
                logging.warning("account needs to be created")
                account = Account(user=user,all_users=[db.Key.from_path("User", user.user_id())],status="new")    
                account.put()
            memcache.set(memcache_key,account)
        logging.warning("account: %s"%account.key())    
        return account
                
    def put_accounts(self,accounts):
        return db.put(accounts)    
    
    @classmethod    
    def _user_key(cls,user):
        return db.Key.from_path("User", user.user_id())     


    # only to be used for migrations that are manual    
    @classmethod    
    def migrate(cls,user_nickname,account):
        accounts = Account.all().fetch(1000)
        user = None
        for account in accounts:
            if account.user.nickname() == user_nickname:
                user = account.user
                break
        # break early if no user        
        if not user: return     
        
        # get the old account that we don't really need   
        old_account = cls().get_current_user(user=user)           
        # add the user to the destination account
        all_users = set(account.all_users)
        all_users.add(user)
        account.all_users = list(all_users)
        account.put()
        
        # delete old account
        old_account.delete()