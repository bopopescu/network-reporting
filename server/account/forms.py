from django import forms
from account.models import Account

class AccountForm(forms.ModelForm):
	class Meta:
		model = Account
		exclude = ('user', 'date_added', 'active')