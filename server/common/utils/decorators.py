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
def whitelist_login_required(function=None):
  """Implementation of Django's login_required decorator.

  The login redirect URL is always set to request.path
  """
  def user_is_active(u):
    from google.appengine.api import users
    from account.query_managers import AccountQueryManager
    return users.is_current_user_admin() or AccountQueryManager.get_current_account().active
  
  
  def login_required_wrapper(request, *args, **kw):
    if not request.user.is_authenticated():
      return HttpResponseRedirect(users.create_login_url(request.path))

    if user_is_active(request.user):
      return function(request, *args, **kw)
    else:
      return HttpResponseRedirect(reverse('account_new'))

  return login_required_wrapper

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
