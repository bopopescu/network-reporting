try:
    from functools import update_wrapper, wraps
except ImportError:
    from django.utils.functional import update_wrapper, wraps  # Python 2.4 fallback.

from django.views.decorators.cache import cache_page

from django.utils.decorators import available_attrs
from django.utils.http import urlquote
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME, logout
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api import users, memcache
from django.core.urlresolvers import reverse
import warnings
import inspect
import logging

from django.views.decorators.vary import vary_on_headers, vary_on_cookie

from django.utils.cache import get_cache_key
# from common.utils.cache import mpcache

#TODO: Rename this function since we no longer use a whitelist
# def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
#     """
#     Decorator for views that checks that the user passes the given test,
#     redirecting to the log-in page if necessary. The test should be a callable
#     that takes the user object and returns True if the user passes.
#     """
#     from account.query_managers import AccountQueryManager
#
#     if not login_url:
#         from django.conf import settings
#         login_url = settings.LOGIN_URL
#
#     def decorator(view_func):
#         def _wrapped_view(request, *args, **kwargs):
#             if test_func(request.user):
#                 # check to see if an account has already been setup
#                 account = AccountQueryManager.get_current_account(user=request.user,create=False)
#                 if account:
#                     return view_func(request, *args, **kwargs)
#                 else:
#                     return HttpResponseRedirect(reverse('registration_register_google'))
#             path = urlquote(request.get_full_path())
#             tup = login_url, redirect_field_name, path
#             return HttpResponseRedirect('%s?%s=%s' % tup)
#         return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
#     return decorator


def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def staff_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_active and u.is_staff,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def conditionally(dec, cond):
    """ Add a decorator if some condition is met """
    def new_dec(f):
        if not cond:
            return f
        return dec(f)
    return new_dec

def cache_page_until_post(time=5*60):
    """ Caches a page until it expires or a post occurs in the session. """
    def wrap(view):
        def new_view(request, *args, **kw):

            page_cache_key = _build_page_cache_key(request)

            if not page_cache_key:
                return view(request, *args, **kw)

            if request.method in ["POST", "PUT"]:
                # If we are POSTing, clear the cache
                session_cache_key = _build_session_cache_key(request)
                session_cache_key_set = memcache.get(session_cache_key) or set()
                for key in session_cache_key_set:
                    memcache.delete(key)

                memcache.delete(session_cache_key)
                return view(request, *args, **kw)

            elif request.method == "GET":
                # If we are GETting, add to cache and also add to list of
                # cached pages to delete on POST
                cached_response = memcache.get(page_cache_key)
                if cached_response:
                    return cached_response
                else:
                    # Build the response
                    view_response = view(request, *args, **kw)
                    memcache_succes = False
                    try:
                        memcache.set(page_cache_key, view_response, time=time)
                        memcache_succes = True
                    except ValueError: # too big
                        memcache_succes = False
                        pass
                    # Add the cached page's key to the list of all the pages
                    # we have cached since the last POST
                    if memcache_succes:
                        session_cache_key = _build_session_cache_key(request)
                        logging.info("session_cache_key: %s" % session_cache_key)
                        session_cache_key_set = memcache.get(session_cache_key)
                        if session_cache_key_set is None:
                            session_cache_key_set = set()
                        session_cache_key_set.add(page_cache_key)

                        memcache.set(session_cache_key,
                                     session_cache_key_set)
                    return view_response

        return new_view
    return wrap

def _build_session_cache_key(request):
    """ Returns a string to key our session cache under. We use the session
        cache to keep track of what needs to be deleted on a post.
        We have a different key for each user """
    session_id = request.COOKIES['sessionid']
    return "session_cache:%s" % str(session_id)

def _build_page_cache_key(request):
    """ We key our page_cache off of the session id and the url """
    # TODO: Should we hash this perhaps? What happens if the qs is very long
    path = request.path
    try:
        session_id = request.COOKIES['sessionid']
    except KeyError:
        return None
    query_string = request.META['QUERY_STRING']
    return "page_cache:%s:%s:%s" % (session_id, path, query_string)

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


class wraps_first_arg(object):
    """ Decorator that wraps all nonlist arguments and turns them into lists.
    Only works for bound methods """
    def __init__(self, f):
        self.f = f
    def __call__(self, *args):
        args = list(args)
        if not isinstance(args[1], (list, tuple)):
            args[1] = [args[1]]

        return self.f(*args)


def returns_unicode(func):
    """ If the result is an unencoded string, encode it. """
    def new_func(*args, **kwargs):
        unencoded = func(*args,**kwargs)
        if isinstance(unencoded, basestring):
            if not isinstance(unencoded, unicode):
                return unicode(unencoded, 'utf-8')
        else:
            return unencoded
    return new_func


def decorate_all_methods(decorator):
    """
    Decorator that applies a decorator to all methods in a class 

    NOTE: This will also wrap nested methods

    Author:
        Haydn (5/21/2012)
    """
    def decorate(cls):
        for method in inspect.getmembers(cls, inspect.ismethod):
            method_name = method[1].__name__
            if 'mptest' in method_name:
                setattr(cls, method_name, decorator(getattr(cls, method_name)))
        return cls
    return decorate
