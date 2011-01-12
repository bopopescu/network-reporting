import logging

from common.utils.cachedquerymanager import CachedQueryManager

from google.appengine.ext import db

from account.models import Account

class AccountQueryManager(CachedQueryManager):
    Model = Account
    def get_by_key_name(self,name):
        return self.Model.get_by_key_name(name)
    def put_accounts(self,accounts):
        return db.put(accounts)    
