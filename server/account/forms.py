from django import forms
from common.utils import forms as mpforms
from account.models import Account

class AccountForm(mpforms.MPModelForm):
  TEMPLATE = 'account/form/account_form.html'
  class Meta:
    model = Account
    exclude = ('user', 'date_added', 'active', 'status')