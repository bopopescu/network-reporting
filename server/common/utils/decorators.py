from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api import users

def whitelist_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in
    and is on the whitelist, redirecting
    to the log-in page if necessary.
    """    
    
    def check_whitelist(u):

      from account.models import Account
      return Account.current_account().active
      
    
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and check_whitelist(u),
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def whitelist_login_required(function=None):
  """Implementation of Django's login_required decorator.

  The login redirect URL is always set to request.path
  """
  def user_is_active(u):
    from google.appengine.api import users
    from account.models import Account
    return Account.current_account().active
  
  
  def login_required_wrapper(request, *args, **kw):
    if request.user.is_authenticated():
      if user_is_active(request.user):
        return function(request, *args, **kw)
      else:
        from django.core.urlresolvers import reverse
        return HttpResponseRedirect(reverse('website_pending'))   
    return HttpResponseRedirect(users.create_login_url(request.path))
  return login_required_wrapper
