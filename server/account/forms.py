from django import forms
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from account.models import Account

class AccountForm(mpforms.MPModelForm):
  TEMPLATE = 'account/form/account_form.html'
  
  phone = mpfields.MPTextField(label="Phone #", required=False)
  
  class Meta:
    model = Account
    exclude = ('user', 'date_added', 'active', 'status')