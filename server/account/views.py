from google.appengine.api import users, mail

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from common.ragendja.template import render_to_response

from common.utils.query_managers import CachedQueryManager
from common.utils.timezones import Pacific_tzinfo

from account.models import Account, PaymentRecord
from account.forms import AccountForm, NetworkConfigForm, PaymentInfoForm
from account.query_managers import AccountQueryManager, PaymentRecordQueryManager
from ad_network_reports.query_managers import AdNetworkMapperManager, \
        AdNetworkStatsManager
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager, AppQueryManager
import logging
from common.utils.request_handler import RequestHandler
from common.utils.decorators import staff_login_required

import urllib2
import string
from common.utils import simplejson
import datetime
from itertools import groupby


class GeneralSettingsHandler(RequestHandler):
    def get(self, *args, **kwargs):
        self.account.paymentinfo = self.account.payment_infos.get()
        user = self.account.mpuser
        return render_to_response(self.request,
                                  "account/general_settings.html",
                                  {
                                      "account": self.account,
                                      "user": user
                                  })

@login_required
def index(request, *args, **kwargs):
    return GeneralSettingsHandler()(request, use_cache=False,
                                    *args, **kwargs)


class AdNetworkSettingsHandler(RequestHandler):
    def get(self, account_form=None):
        if self.params.get("skip"):
            self.account.status = "step4"
            AccountQueryManager.put_accounts(self.account)
            return HttpResponseRedirect(reverse('advertiser_campaign'))

        account_form = account_form or AccountForm(instance=self.account)
        apps_for_account = AppQueryManager.get_apps(account=self.account)
        user = self.account.mpuser

        networks = ['admob_status',
                    'adsense_status',
                    'brightroll_status',
                    'ejam_status',
                    'greystripe_status',
                    'inmobi_status',
                    'jumptap_status',
                    'millennial_status',
                    'mobfox_status']
        network_config_status = {}

        def _get_net_status(account, network):
            status = 0
            # eg. account.admob_pub_id
            if getattr(account.network_config, network[:-6] + 'pub_id', None):
                for app in apps_for_account:
                    if getattr(app.network_config, network[:-6] + 'pub_id', None):
                        status = 2
                        return status
                status = 1
                return status
            broke = False
            for app in apps_for_account:
                # dynamically attach adunits to app
                app.adunits = AdUnitQueryManager.get_adunits(app=app)
                if  not getattr(app.network_config, network[:-6] + 'pub_id', None):
                    broke = True
                else:
                    status = 3
            if not broke and len(apps_for_account) != 0:
                return 4
            else:
                return status

        for network in networks:
            network_config_status[network] = _get_net_status(self.account, network)

        return render_to_response(self.request,
                                  'account/ad_network_settings.html',
                                  dict({'account': self.account,
                                        'account_form': account_form,
                                        'user': user,
                                        "apps": apps_for_account}.items() + network_config_status.items()))

    def post(self):
        account_form = AccountForm(data=self.request.POST, instance=self.account)
        network_config_form = NetworkConfigForm(data=self.request.POST, instance=self.account.network_config)

        if account_form.is_valid():
            PUB_ID = '_pub_id'
            # Index AdNetworkLoginCredentials by ad network name
            account = AccountQueryManager.get_account_by_key(self.account.key())
            logins = account.login_credentials
            logins_dict = {}
            for login in logins:
                logins_dict[login.ad_network_name] = login

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
                        # Create an AdNetworkAppMapper if there exists a login
                        # for the network (safe to re-create if it already
                        # exists)
                        network = app_key_identifier[1][:-len(PUB_ID)]
                        if value and network in logins_dict:
                            mappers = AdNetworkMapperManager.get_mappers_for_app(
                                    login=logins_dict[network], app=app)
                            # Delete the existing mappers if there are no scrape
                            # stats for them.
                            for mapper in mappers:
                                if mapper:
                                    stats = mapper.ad_network_stats
                                    if not stats.count(limit=1):
                                        mapper.delete()
                            AdNetworkMapperManager.create(network=network,
                                    pub_id=value, login=logins_dict[network],
                                    app=app)

                app_form = NetworkConfigForm(data=app_network_config_data,
                        instance=app.network_config)
                app_network_config = app_form.save(commit=False)
                AppQueryManager.update_config_and_put(app, app_network_config)

                adunits = AdUnitQueryManager.get_adunits(app=app)
                for adunit in adunits:
                    adunit_network_config_data = {}
                    for (key, value) in self.request.POST.iteritems():
                        adunit_key_identifier = key.split('-_ADUNIT_-')
                        if adunit_key_identifier[0] == str(adunit.key()):
                            adunit_network_config_data[adunit_key_identifier[1]] = value
                    adunit_form = NetworkConfigForm(data=adunit_network_config_data, instance=adunit.network_config)
                    adunit_network_config = adunit_form.save(commit=False)
                    AdUnitQueryManager.update_config_and_put(adunit, adunit_network_config)

            if self.account.status == "step3":
                self.account.status = "step4"
                AccountQueryManager.put_accounts(self.account)
                return HttpResponseRedirect(reverse('advertiser_campaign'))

        return self.get(account_form=account_form)


@login_required
def ad_network_settings(request, *args, **kwargs):
    return AdNetworkSettingsHandler()(request, *args, **kwargs)


class CreateAccountHandler(RequestHandler):
    def get(self, account_form=None):
        account_form = account_form or AccountForm(instance=self.account)
        return render_to_response(self.request, 'account/new_account.html', {'account': self.account,
                                                                           'account_form': account_form})

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
            account.display_new_networks = True
            AccountQueryManager().put_accounts(account)

            # Step 2
            return HttpResponseRedirect(reverse('publisher_create_app'))

        return self.get(account_form=account_form)


# We use login_required here since we want to let users activate themselves on this page
@login_required
def create_account(request, *args, **kwargs):
    return CreateAccountHandler()(request, *args, **kwargs)


class LogoutHandler(RequestHandler):
    def get(self):
        return HttpResponseRedirect(users.create_logout_url('/main/'))


def logout(request, *args, **kwargs):
    return LogoutHandler()(request, *args, **kwargs)


class PaymentInfoChangeHandler(RequestHandler):
    def get(self, payment_form=None, *args, **kwargs):
        form = payment_form or PaymentInfoForm(instance=self.account.payment_infos.get())
        success_banner = kwargs['success_banner'] if 'success_banner' in kwargs else False
        return render_to_response(self.request,
                                  'account/paymentinfo_change.html',
                                  {'form': form, 'success_banner':success_banner})

    def post(self, *args, **kwargs):
        form = PaymentInfoForm(self.request.POST, instance=self.account.payment_infos.get())
        if form.is_valid():
            if not form.instance:
                account = self.account
            else:
                account = form.instance.account
            payment_info = form.save(commit=False)
            payment_info.account = account
            payment_info.put()
            return redirect('payment_info_change_success')
        return self.get(payment_form=form)


@login_required
def payment_info_change(request, *args, **kwargs):
    return PaymentInfoChangeHandler()(request, *args, **kwargs)

@login_required
def payment_info_change_success(request, *args, **kwargs):
    kwargs['success_banner'] = True
    return PaymentInfoChangeHandler()(request, *args, **kwargs)


class PaymentHistoryHandler(RequestHandler):
    def get(self, *args, **kwargs):
        # Handle scheduled payment resolution via GET parameter
        if self.request.GET.get("resolved"):
            record = PaymentRecordQueryManager.get(self.request.GET.get("resolved"))
            if record:
                record.resolved = True
                record.put()

        balance = 0
        total_paid = 0
        start_date = datetime.date(2011, 9, 1)  # Earliest date that we pull stats for
        end_date = datetime.datetime.now(Pacific_tzinfo())

        payment_records = PaymentRecordQueryManager().get_payment_records(account=self.account.key())
        if payment_records:
            payment_records = sorted(payment_records, key=lambda record: record.period_start, reverse=True)
            start_date = payment_records[0].period_end + datetime.timedelta(days=1)
            total_paid = sum([payment.amount for payment in payment_records])

        scheduled_payments = PaymentRecordQueryManager().get_scheduled_payments(account=self.account.key())
        if scheduled_payments:
            scheduled_payments = sorted(scheduled_payments, key=lambda record: record.period_start)
            start_date = scheduled_payments[-1].period_end + datetime.timedelta(days=1)
            balance = sum([payment.amount for payment in scheduled_payments])

        earnings = get_balance(self.account.key(), start_date, end_date)
        unscheduled_balance = earnings['sum']['rev']
        balance += unscheduled_balance

        return render_to_response(self.request,
                                  'account/payment_history.html',
                                  {'payment_records': payment_records,
                                   'scheduled_payments': scheduled_payments,
                                   'balance': balance,
                                   'total_paid': total_paid,
                                   'unscheduled_balance': unscheduled_balance,
                                   'start_date': start_date,
                                   'end_date': end_date})

    def post(self, *args, **kwargs):
        payment = PaymentRecord()
        period_start = datetime.datetime.strptime(self.request.POST.get("period_start"), "%m/%d/%Y").date()
        period_end = datetime.datetime.strptime(self.request.POST.get("period_end"), "%m/%d/%Y").date()

        if period_start and period_end:
            payment.account = self.account
            payment.period_start = period_start
            payment.period_end = period_end
            # Convert dollars to float. eg. '$2,313.20' becomes '2313.20'
            amount = ''.join([c for c in self.request.POST.get("amount") if c in string.digits + '.'])
            payment.amount = float(amount)
            payment.status = self.request.POST.get("status")
            if self.request.POST.get("date_executed"):
                payment.date_executed = datetime.datetime.strptime(self.request.POST.get("date_executed"),
                                                                    "%m/%d/%Y")
            if self.request.POST.get("form_type") == "scheduled_payment":
                payment.scheduled_payment = True
            payment.put()

        return self.get()


def get_balance(pub_id, start_date, end_date):
    url = "http://mpx.mopub.com/stats/pub" + \
          "?pub=" + str(pub_id) + \
          "&start=" + start_date.strftime("%m-%d-%Y") + \
          "&end=" + end_date.strftime("%m-%d-%Y")

    try:
        data = urllib2.urlopen(url).read()
    except (urllib2.URLError, IOError):
        return {'daily': [], 'sum': {'imp': 0, 'rev': 0}}

    return simplejson.loads(data)


@login_required
def payment_history(request, *args, **kwargs):
    return PaymentHistoryHandler()(request, *args, **kwargs)


class PaymentRecordDelete(RequestHandler):
    def get(self, payment_record_key):
        payment_record = PaymentRecordQueryManager.get(payment_record_key)
        PaymentRecord.delete(payment_record)
        next = self.request.GET.get('next') or reverse('payment_history')
        return HttpResponseRedirect(next)


@staff_login_required
def payment_delete(request, *args, **kwargs):
    return PaymentRecordDelete()(request, *args, **kwargs)
