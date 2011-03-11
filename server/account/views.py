from google.appengine.api import users, mail

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response

from common.utils.decorators import whitelist_login_required
from common.utils.cachedquerymanager import CachedQueryManager

from account.models import Account
from account.forms import AccountForm
from account.query_managers import AccountQueryManager
from publisher.query_managers import AdUnitQueryManager

class RequestHandler(object):
    def __call__(self,request,*args,**kwargs):
        self.params = request.POST or request.GET
        self.request = request
        self.account = None
        user = users.get_current_user()
        if user:
          if users.is_current_user_admin():
            account_key_name = request.COOKIES.get("account_impersonation",None)
            if account_key_name:
              self.account = AccountQueryManager().get_by_key_name(account_key_name)
        if not self.account:  
          self.account = Account.current_account()
          
        if request.method == "GET":
            return self.get(*args,**kwargs)
        elif request.method == "POST":
            return self.post(*args,**kwargs)    
    def get(self):
        pass
    def put(self):
        pass  


class AccountHandler(RequestHandler):
  def get(self,account_form=None):
    if self.params.get("skip"):
      self.account.status = "step4"
      AccountQueryManager().put_accounts(self.account)
      return HttpResponseRedirect(reverse('advertiser_campaign'))

    account_form = account_form or AccountForm(instance=self.account, prefix="account")
    return render_to_response(self.request,'account/account.html', {'account': self.account,
                                                                    'account_form': account_form})

  def post(self):
    account_form = AccountForm(data=self.request.POST, instance=self.account, prefix="account")

    if account_form.is_valid():
      account = account_form.save(commit=False)
      AccountQueryManager().put_accounts(account)
      adunits = AdUnitQueryManager().get_adunits(account=account)
      CachedQueryManager().cache_delete(adunits)
      
      if self.account.status == "step3":
        self.account.status = "step4"
        AccountQueryManager().put_accounts(self.account)
        return HttpResponseRedirect(reverse('advertiser_campaign'))
    
    return self.get(account_form=account_form)    
    # return render_to_response(self.request,'account/account.html', {'account': self.account})

@whitelist_login_required     
def index(request,*args,**kwargs):
  return AccountHandler()(request,*args,**kwargs)

class NewAccountHandler(RequestHandler):
  def get(self,account_form=None):
    mail.send_mail(sender="olp@mopub.com",
                   to="beta@mopub.com",
                   subject="New User",
                   body="%s has signed up for an account."%self.request.user.email)
    account_form = account_form or AccountForm(instance=self.account, prefix="account")
    return render_to_response(self.request,'account/new_account.html',{'account': self.account,
                                                               'account_form' : account_form })
  def post(self):
    account_form = AccountForm(data=self.request.POST, instance=self.account, prefix="account")
    # Make sure terms and conditions are agreed to
    if not self.request.POST.get("terms_conditions"):
      account_form.term_conditions_error = "Accept the terms and conditions in order to start using MoPub."
      return self.get(account_form=account_form)  

    if account_form.is_valid():
      account = account_form.save(commit=False)
      
      # Go ahead and activate the account
      account.active = True
      AccountQueryManager().put_accounts(account)
      
      # send a reply
      mail.send_mail(sender="MoPub Team <olp@mopub.com>",
                     reply_to="sales@mopub.com",
                     to="self.request.user.email",
                     subject="Welcome to MoPub",
                     body="""Hello from MoPub!

MoPub is designed to help mobile publishers monetize their apps more 
effectively. If you have any questions during the setup process,
please don't hesitate to email our sales department at sales@mopub.com.

Thanks,
The MoPub Team
""")
      
      return HttpResponseRedirect(reverse('publisher_app_create'))

    return self.get(account_form=account_form)
    
# We use login_required here since we want to let users activate themselves on this page
@login_required
def new(request,*args,**kwargs):
  return NewAccountHandler()(request,*args,**kwargs)  

class LogoutHandler(RequestHandler):
  def get(self):
    return HttpResponseRedirect(users.create_logout_url('/main/'))
    
def logout(request,*args,**kwargs):
  return LogoutHandler()(request,*args,**kwargs)
