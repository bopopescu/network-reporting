from common.utils import djangoforms
from models import AdNetworkLoginCredentials

class LoginInfoForm(djangoforms.ModelForm):
    send_email = djangoforms.BooleanProperty()

    def __unicode__(self):
        return str(self.fields)
    class Meta:
        model = AdNetworkLoginCredentials
        fields = ('ad_network_name', 'username', 'password', 'client_key')