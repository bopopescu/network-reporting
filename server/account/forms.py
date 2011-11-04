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
        exclude = ("rev_share", "price_floor", "blocklist")

    # def clean(self):
    #     cleaned_data = self.cleaned_data
    #     for key, value in cleaned_data.iteritems():
    #         cleaned_data[key] = value.strip() if value else value
    #     return cleaned_data


class PaymentInfoForm(mpforms.MPModelForm):
    TEMPLATE = "account/form/paymentinfo_form.html"
    country = mpfields.MPChoiceField(required=True, widget=mpwidgets.MPSelectWidget, choices=ISO_COUNTRIES)
    payment_preference = mpfields.MPChoiceField(required=True,
                                                widget=mpwidgets.MPRadioWidget,
                                                choices=(('paypal', 'Paypal'), ('wire', 'Wire Transfer')))

    class Meta:
        model = PaymentInfo
        fields = ('country',
                  'business_name',
                  'payment_preference',
                  'us_tax_id',
                  'local_tax_id',
                  'paypal_email',
                  'beneficiary_name',
                  'bank_name',
                  'bank_address',
                  'account_number',
                  'ach_routing_number',
                  'bank_swift_code',)

    def clean_payment_type(self):
        if self.data['payment_preference'] == 'paypal' and \
           self.data['paypal_email'] == '':
            raise forms.ValidationError('Please provide your Paypal account information if you wish to use Paypal.')


    def clean_country_information(self):
        if self.data['payment_preference'] == 'wire':
            if self.data['country'] == 'US':
                required_us_info = [self.data['us_tax_id'],
                                    self.data['ach_routing_number']]

                if not all(required_us_info):
                    raise forms.ValidationError("""The following information is required for accounts in the United States:
                                                US Tax ID
                                                ACH Routing Number
                                                """)
            else:
                required_us_info = [self.data['local_tax_id'],
                                    self.data['bank_swift_code']]

                if not all(required_us_info):
                    raise forms.ValidationError("""The following information is required for accounts outside the United States:
                                                US Tax ID
                                                Bank SWIFT Code
                                                """)

    def clean(self, *args, **kwargs):
        self.clean_payment_type()
        self.clean_country_information()
        return super(PaymentInfoForm, self).clean(*args, **kwargs)