from google.appengine.api import users, mail

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response

from common.utils.decorators import whitelist_login_required
from common.utils.query_managers import CachedQueryManager

from account.models import Account
from account.forms import AccountForm
from account.query_managers import AccountQueryManager
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

from common.utils.request_handler import RequestHandler

class AccountHandler(RequestHandler):
    def get(self,account_form=None):
        if self.params.get("skip"):
            self.account.status = "step4"
            AccountQueryManager.put_accounts(self.account)
            return HttpResponseRedirect(reverse('advertiser_campaign'))

        account_form = account_form or AccountForm(instance=self.account)
        return render_to_response(self.request,'account/account.html', {'account': self.account, 'account_form': account_form})

    def post(self):
        account_form = AccountForm(data=self.request.POST, instance=self.account)

        if account_form.is_valid():
            account = account_form.save(commit=False)

            AccountQueryManager.put_accounts(account)
            
            if self.account.status == "step3":
                self.account.status = "step4"
                AccountQueryManager.put_accounts(self.account)
                return HttpResponseRedirect(reverse('advertiser_campaign'))
        
        return self.get(account_form=account_form)        

@whitelist_login_required         
def index(request,*args,**kwargs):
    return AccountHandler()(request,*args,**kwargs)

class NewAccountHandler(RequestHandler):
    def get(self,account_form=None):
        account_form = account_form or AccountForm(instance=self.account)
        return render_to_response(self.request,'account/new_account.html',{'account': self.account,
                                                                           'account_form' : account_form })
    def post(self):
        account_form = AccountForm(data=self.request.POST, instance=self.account)
        # Make sure terms and conditions are agreed to
        if not self.request.POST.get("terms_conditions"):
            account_form.term_conditions_error = "Accept the terms and conditions in order to start using MoPub."
            return self.get(account_form=account_form)    

        if account_form.is_valid():
            account = account_form.save(commit=False)
            
            # Go ahead and activate the account
            account.active = True
            AccountQueryManager().put_accounts(account)

            # Step 2
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
