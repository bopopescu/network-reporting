from google.appengine.api import users, mail

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response

from common.utils.query_managers import CachedQueryManager

from account.models import Account
from account.forms import AccountForm, NetworkConfigForm
from account.query_managers import AccountQueryManager
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager, AppQueryManager
import logging
from common.utils.request_handler import RequestHandler

class AccountHandler(RequestHandler):
    def get(self,account_form=None):
        if self.params.get("skip"):
            self.account.status = "step4"
            AccountQueryManager.put_accounts(self.account)
            return HttpResponseRedirect(reverse('advertiser_campaign'))
        account_form = account_form or AccountForm(instance=self.account)
        apps_for_account = AppQueryManager.get_apps(account=self.account)
        
        return render_to_response(self.request,'account/account.html', {'account': self.account, 
                                                                        'account_form': account_form,
                                                                        "apps": apps_for_account})

    def post(self):
        account_form = AccountForm(data=self.request.POST, instance=self.account)
        network_config_form = NetworkConfigForm(data=self.request.POST, instance=self.account.network_config)
        
        if account_form.is_valid():
            account = account_form.save(commit=False)
            network_config = network_config_form.save(commit=False)
            AccountQueryManager.update_config_and_put(account, network_config)

            apps_for_account = AppQueryManager.get_apps(account=self.account)
            # Build app level pub_ids
            for app in apps_for_account:
                app_network_config_data = {}
                for (key, value) in self.request.POST.iteritems():
                    app_key_identifier = key.split('-__-')
                    if app_key_identifier[0] == str(app.key()):
                        app_network_config_data[app_key_identifier[1]] = value
                
                logging.warning("link" + unicode(app.name) + " " + str(app_network_config_data))
                app_form = NetworkConfigForm(data=app_network_config_data, instance=app.network_config)
                app_network_config = app_form.save(commit=False)
                AppQueryManager.update_config_and_put(app, app_network_config)
                        
            
            if self.account.status == "step3":
                self.account.status = "step4"
                AccountQueryManager.put_accounts(self.account)
                return HttpResponseRedirect(reverse('advertiser_campaign'))
        return self.get(account_form=account_form)        

@login_required         
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
