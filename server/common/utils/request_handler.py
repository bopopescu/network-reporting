import datetime

from account.query_managers import AccountQueryManager

from google.appengine.ext import db

from inspect import getargspec

from common.utils import simplejson
from common.utils.decorators import conditionally, cache_page_until_post
from common.utils.timezones import Pacific_tzinfo
from common.utils import date_magic

from django.conf import settings
from django.http import Http404
from common.ragendja.template import render_to_response

from stats.log_service import LogService

audit_logger = LogService(blob_file_name='audit', flush_lines=1)


class RequestHandler(object):
    """ Does some basic work and redirects a view to get and post
    appropriately """
    def __init__(self, request=None, login=True, template=None, id=None):
        self._id = id
        self.obj = None
        self.login = login
        self.template = template
        if request:
            self.request = request
            if self.login:
                self._set_account()

        super(RequestHandler, self).__init__()

    def __call__(self, request, cache_time=5 * 60, use_cache=True, *args, **kwargs):
        if settings.DEBUG:
            use_cache = False

        # Initialize our caching decorator
        cache_dec = cache_page_until_post(time=cache_time)

        # Apply the caching decorator conditionally
        @conditionally(cache_dec, use_cache)
        # @cache_page(cache_time)
        def mp_view(request, *args, **kwargs):
            """
            We wrap all the business logic of the request Handler here
            in order to be able to properly use the cache decorator
            """

            # Set the basics
            self.params = request.POST or request.GET
            self.request = request or self.request

            # date ranges are used very commonly, so compute them
            # beforehand here to keep things dry.
            # we set:
            # * self.start_date - the first date in the range
            # * self.end_date - the last date in the range
            # * self.date_range - the number of days in between
            #       self.start_date and self.end_date, inclusive.
            # * self.days - a list of datetime.date objects for each day
            #       in between self.start_date and self.end_date, inclusive.
            self.start_date, self.end_date = get_start_and_end_dates(self.request)
            try:
                self.date_range = int(self.params.get('r'))
            except:
                self.date_range = 14
            self.days = date_magic.gen_days(self.start_date, self.end_date)

            # Set self.account
            if self.login:
                if 'account' in self.params:
                    account_key = self.params['account']
                    if account_key:
                        self.account = AccountQueryManager.get(account_key)
                else:
                    self._set_account()

            # If a key is passed in the url, and if the request handler
            # has been initialized with id='key_name', we can fetch the
            # object from the db now.  We'll use it later on to make sure
            # the user requesting the object is actually the object's
            # owner.
            if self._id:
                db_object_key = kwargs.get(self._id)
                self.obj = db.get(db_object_key)

                # ensure that the fetched object's owner is the same
                # as the user making the request.
                if self.obj._account != self.account.key():
                    raise Http404

            # Set self.offline (use the offline stats)
            # XXX: what are offline stats?
            self.offline = self.params.get("offline", False)
            self.offline = True if self.offline == "1" else False

            # Now we can define get/post methods with variables
            # instead of having to get it from the Query dict
            # every time! hooray!
            if request.method == "GET":
                f_args = getargspec(self.get)[0]
                for arg in f_args:
                    if not arg in kwargs and arg in self.params:
                        kwargs[arg] = self.params.get(arg)

                response = self.get(*args, **kwargs)
                if not isinstance(response, dict):
                    return response
                response.update({
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "date_range": self.date_range,
                    "days": self.days,
                    "offline": self.offline,
                    "account": self.account,
                    "True": True,
                    "False": False,
                })
                return render_to_response(self.request,
                                          self.template,
                                          response)

            elif request.method == "POST":
                if self.login and self.request.user.is_authenticated():
                    # XXX: why do we do this?
                    audit_logger.log(simplejson.dumps({
                        "user_email": self.request.user.email,
                        "account_email": self.account.mpuser.email,
                        "account_key": str(self.account.key()),
                        "time": datetime.datetime.now(Pacific_tzinfo()).isoformat(),
                        "url": self.request.get_full_path(),
                        "body": request.POST}))
                f_args = getargspec(self.post)[0]
                for arg in f_args:
                    if not arg in kwargs and arg in self.params:
                        kwargs[arg] = self.params.get(arg)
                return self.post(*args, **kwargs)

            elif request.method == "PUT":
                f_args = getargspec(self.put)[0]
                for arg in f_args:
                    if not arg in kwargs and arg in self.params:
                        kwargs[arg] = self.params.get(arg)
                return self.put(*args, **kwargs)

            elif request.method == "DELETE":
                f_args = getargspec(self.delete)[0]
                for arg in f_args:
                    if not arg in kwargs and arg in self.params:
                        kwargs[arg] = self.params.get(arg)
                return self.delete(*args, **kwargs)

        # Execute our newly decorated view
        return mp_view(request, *args, **kwargs)

    def get(self):
        raise NotImplementedError

    def put(self):
        raise NotImplementedError

    def _set_account(self):
        self.account = None
        user = self.request.user
        if user:
            if user.is_staff:
                account_key = self.request.COOKIES.get("account_impersonation", None)
                if account_key:
                    self.account = AccountQueryManager.get(account_key)
        if not self.account:
            self.account = AccountQueryManager.get_current_account(self.request, cache=True)


class AjaxRequestHandler(RequestHandler):
    pass


def get_start_and_end_dates(request):
    start_date_string = request.GET.get('s', None)
    date_range = abs(int(request.GET.get('r', 14)))

    if start_date_string:
        year, month, day = str(start_date_string).split('-')
        start_date = datetime.date(int(year), int(month), int(day))
        end_date = start_date + datetime.timedelta(date_range - 1)
    else:
        end_date = datetime.datetime.now(Pacific_tzinfo()).date()
        start_date = end_date - datetime.timedelta(date_range - 1)

    return (start_date, end_date)
