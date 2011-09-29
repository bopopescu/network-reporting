import logging
from datetime import date,datetime

from account.query_managers import AccountQueryManager
from account.models import Account

from google.appengine.api import users
from google.appengine.ext import db

from inspect import getargspec

from common.utils import simplejson
from common.utils.decorators import cache_page_until_post, conditionally
from common.utils.timezones import Pacific_tzinfo
from django.views.decorators.cache import cache_page
from django.conf import settings

from stats.log_service import LogService

audit_logger = LogService(blob_file_name='audit', flush_lines=1)

class RequestHandler(object):
    """ Does some basic work and redirects a view to get and post appropriately """
    def __init__(self, request=None, login=True):
        self.login = login
        if request:
            self.request = request
            if self.login:
                self._set_account()

        super(RequestHandler,self).__init__()

    def __call__(self,request, cache_time=5*60, use_cache=True, *args,**kwargs):
        if settings.DEBUG:
            use_cache = False

        # Initialize our caching decorator
        cache_dec = cache_page_until_post(time=cache_time)

        # Apply the caching decorator conditionally
        @conditionally(cache_dec, use_cache)
        # @cache_page(cache_time)
        def mp_view(request, *args, **kwargs):
            """ We wrap all the business logic of the request Handler here
                in order to be able to properly use the cache decorator """
            self.params = request.POST or request.GET
            self.request = request or self.request

            try:
              self.date_range = int(self.params.get('r'))  # date range
            except:
              self.date_range = 14

            try:
              s = self.request.GET.get('s').split('-')
              self.start_date = date(int(s[0]),int(s[1]),int(s[2]))
            except:
              self.start_date = None

            if self.login:
                if self.params.has_key('account'):
                    account_key = self.params['account']
                    if account_key:
                      self.account = AccountQueryManager.get(account_key)
                else:
                    self._set_account()

                logging.info("final account: %s"%(self.account.key()))
                logging.info("final account: %s"%repr(self.account.key()))

            # use the offline stats
            self.offline = self.params.get("offline",False)
            self.offline = True if self.offline == "1" else False

            if request.method == "GET":
                # Now we can define get/post methods with variables instead of having to get it from the
                # Query dict every time! hooray!
                f_args = getargspec(self.get)[0]
                for arg in f_args:
                    if not kwargs.has_key(arg) and self.params.has_key(arg):
                        kwargs[arg] = self.params.get(arg)
                return self.get(*args,**kwargs)
            elif request.method == "POST":
                # Now we can define get/post methods with variables instead of having to get it from the
                # Query dict every time! hooray!
                if self.login and self.request.user.is_authenticated():
                    audit_logger.log(simplejson.dumps({"user_email": self.request.user.email,
                                                       "account_email": self.account.mpuser.email,
                                                       "account_key": str(self.account.key()),
                                                       "time": datetime.now(Pacific_tzinfo()).isoformat(),
                                                       "url": self.request.get_full_path(),
                                                       "body": request.POST}))
                f_args = getargspec(self.post)[0]
                for arg in f_args:
                    if not kwargs.has_key(arg) and self.params.has_key(arg):
                        kwargs[arg] = self.params.get(arg)
                return self.post(*args,**kwargs)

        # Execute our newly decorated view
        return mp_view(request, *args, **kwargs)


    def get(self):
        raise NotImplementedError

    def put(self):
        raise NotImplementedError

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


class AjaxRequestHandler(RequestHandler):
    pass
