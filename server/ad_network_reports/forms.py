from common.utils import djangoforms
from common.utils import fields as mpfields
from models import AdNetworkLoginCredentials

class LoginInfoForm(djangoforms.ModelForm):
    password2 = mpfields.MPTextField()

    def __unicode__(self):
        return str(self.fields)
    class Meta:
        model = AdNetworkLoginCredentials
        fields = ('ad_network_name', 'username', 'client_key')
