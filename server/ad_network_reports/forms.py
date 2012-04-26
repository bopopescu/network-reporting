from common.utils import djangoforms
from django import forms
from common.utils import fields as mpfields
from django.forms.widgets import TextInput
from models import AdNetworkLoginCredentials

LABEL_NETWORK_TRANSLATION = {'inmobi': ('Access ID:', 'Secret Key:'),}

class LoginCredentialsForm(forms.ModelForm):
    username_str = forms.CharField(label='Username:',
                                   required=False)
    password_str = forms.CharField(label='Password:',
                                   required=False,
                                   widget=forms.PasswordInput)
    client_key = forms.CharField(label='Client Key:',
                                 required=False)

    def __init__(self, *args, **kwargs):
        network = False
        if 'network' in kwargs:
            network = kwargs['network']
            del(kwargs['network'])
        super(LoginCredentialsForm, self).__init__(*args, **kwargs)
        if network and network in LABEL_NETWORK_TRANSLATION:
            self.fields['username_str'].label = \
                    LABEL_NETWORK_TRANSLATION[network][0]
            self.fields['password_str'].label = \
                    LABEL_NETWORK_TRANSLATION[network][1]

    def __unicode__(self):
        return str(self.fields)
    class Meta:
        model = AdNetworkLoginCredentials
        fields = ('client_key')
        # Password is excluded because we never get an encrypted password from
        # the front-end and it must be encrypted in the db.
        exclude = ('account', 'password', 'password_iv', 'username',
                'username-iv')
