from django import forms
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from account.models import Account, NetworkConfig, PaymentInfo
from common.constants import (ISO_COUNTRIES, US_STATES)

class AccountForm(mpforms.MPModelForm):
    TEMPLATE = 'account/form/account_form.html'
    countries = ISO_COUNTRIES
    states = US_STATES

    phone = mpfields.MPTextField(label="Phone #", required=False)
    class Meta:
        model = Account
        fields = ("admob_pub_id",
                  "adsense_pub_id",
                  "adsense_company_name",
                  "adsense_test_mode",
                  "brightroll_pub_id",
                  "chartboost_pub_id",
                  "ejam_pub_id",
                  "greystripe_pub_id",
                  "inmobi_pub_id",
                  "jumptap_pub_id",
                  "millenial_pub_id",
                  "mobfox_pub_id",
                  )

class NetworkConfigForm(mpforms.MPModelForm):

    class Meta:
        model = NetworkConfig

    def clean(self):
        cleaned_data = self.cleaned_data
        for key, value in cleaned_data.iteritems():
            cleaned_data[key] = value.strip() if value else value
        return cleaned_data


class PaymentInfoForm(mpforms.MPModelForm):
    TEMPLATE = "account/form/paymentinfo_form.html"
    country = mpfields.MPChoiceField(required=True, widget=mpwidgets.MPSelectWidget, choices=ISO_COUNTRIES)
    payment_preference = mpfields.MPChoiceField(required=True,
                                                widget=mpwidgets.MPRadioWidget,
                                                choices=(('paypal', 'Paypal'), ('wire', 'Wire Transfer')))

    class Meta:
        model = PaymentInfo
        fields = ('country',
                  'payment_preference',
                  'us_tax_id',
                  'local_tax_id',
                  'paypal_email,',
                  'beneficiary_name',
                  'bank_name',
                  'bank_address',
                  'account_number',
                  'ach_routing_number',
                  'bank_swift_code',)
