try:
    from functools import update_wrapper, wraps
except ImportError:
    from django.utils.functional import update_wrapper, wraps  # Python 2.4 fallback.

from django.utils.decorators import available_attrs
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api import users
from django.core.urlresolvers import reverse
import warnings
import inspect
import logging

#TODO: Rename this function since we no longer use a whitelist
def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    from account.query_managers import AccountQueryManager
    
    if not login_url:
        from django.conf import settings
        login_url = settings.LOGIN_URL

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                # check to see if an account has already been setup
                account = AccountQueryManager.get_current_account(user=request.user,create=False)
                if account:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseRedirect(reverse('registration_register_google'))    
            path = urlquote(request.get_full_path())
            tup = login_url, redirect_field_name, path
            return HttpResponseRedirect('%s?%s=%s' % tup)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator


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

def webdec():
    #if we want to include stuff inside this webdec, have a field day
    def outer_wrap( f ):
        def inner_wrap( request, *args, **kwargs ):
            #do things with the request and stuf here
            #Lots of cool things can be done here,
            #ideally f( blah ) returns a dictionary, which is then used to render the appropriate template.  This way we don't have to keep writing render_to_template blah blah blah, right now since we DO do that, just return it
            return f( **kwargs )
        return inner_wrap
    return outer_wrap

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
