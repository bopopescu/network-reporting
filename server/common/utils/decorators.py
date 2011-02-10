from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api import users
from django.core.urlresolvers import reverse

#TODO: Rename this function since we no longer use a whitelist
def whitelist_login_required(function=None):
  """Implementation of Django's login_required decorator.

  The login redirect URL is always set to request.path
  """
  def user_is_active(u):
    from google.appengine.api import users
    from account.models import Account
    return users.is_current_user_admin() or Account.current_account().active
  
  
  def login_required_wrapper(request, *args, **kw):
    if not request.user.is_authenticated():
      return HttpResponseRedirect(users.create_login_url(request.path))

    if user_is_active(request.user):
      return function(request, *args, **kw)
    else:
      return HttpResponseRedirect(reverse('account_new'))

  return login_required_wrapper
