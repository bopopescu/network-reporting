import logging

from account.query_managers import AccountQueryManager
from google.appengine.api import users
from google.appengine.ext import db
from account.models import Account


class RequestHandler(object):
    def __init__(self,request=None):
      if request:
        self.request = request
        self._set_account()    

      super(RequestHandler,self).__init__()  

    def __call__(self,request,*args,**kwargs):
        self.params = request.POST or request.GET
        self.request = request or self.request
        
        try:
          # Limit date range to 31 days, otherwise too heavy
          self.date_range = min(int(self.params.get('r')),31)  # date range
        except:
          self.date_range = 14
          
        try:
          s = self.request.GET.get('s').split('-')
          self.start_date = date(int(s[0]),int(s[1]),int(s[2]))
        except:
          self.start_date = None
        
        self._set_account()
        
        logging.info("final account: %s"%(self.account.key()))  
        logging.info("final account: %s"%repr(self.account.key()))
          
        # use the offline stats  
        self.offline = self.params.get("offline",False)   
        self.offline = True if self.offline == "1" else False

        if request.method == "GET":
            return self.get(*args,**kwargs)
        elif request.method == "POST":
            return self.post(*args,**kwargs)    
    def get(self):
        pass
    def put(self):
        pass  
        
    def _set_account(self):
        self.account = None
        user = users.get_current_user()
        if user:
          if users.is_current_user_admin():
            account_key = self.request.COOKIES.get("account_impersonation",None)
            if account_key:
              self.account = AccountQueryManager.get(account_key)
        if not self.account:  
          self.account = AccountQueryManager.get_current_account(self.request,cache=True)
            
