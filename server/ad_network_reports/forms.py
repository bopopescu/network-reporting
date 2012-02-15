from common.utils import djangoforms
from django import forms
from common.utils import fields as mpfields
from django.forms.widgets import TextInput
from models import AdNetworkLoginCredentials

class LoginCredentialsForm(forms.ModelForm):
    username_str = forms.CharField(label='Username:', required=False)
    password_str = forms.CharField(label='Password:', required=False)
    client_key = forms.CharField(label='Client Key:', required=False)

    def __unicode__(self):
        return str(self.fields)
    class Meta:
        model = AdNetworkLoginCredentials
        fields = ('client_key')
        # Password is excluded because we never get an encrypted password from
        # the front-end and it must be encrypted in the db.
        exclude = ('account', 'password', 'password_iv', 'username',
                'username-iv')
