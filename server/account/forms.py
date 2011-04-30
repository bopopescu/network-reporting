from django import forms
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from account.models import Account
from common.constants import (ISO_COUNTRIES, US_STATES)

class AccountForm(mpforms.MPModelForm):
    TEMPLATE = 'account/form/account_form.html'
    countries = ISO_COUNTRIES
    states = US_STATES
    
    phone = mpfields.MPTextField(label="Phone #", required=False)
    
    class Meta:
        model = Account
        exclude = ('user', 'all_users', 'date_added', 'active', 'status')