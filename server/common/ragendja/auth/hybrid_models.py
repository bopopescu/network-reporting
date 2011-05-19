from django.utils.translation import ugettext_lazy as _
from google.appengine.ext import db
from common.ragendja.auth.google_models import GoogleUserTraits

class User(GoogleUserTraits):
    """User class that provides support for Django and Google @login_required."""
    user = db.UserProperty()
    username = db.StringProperty(required=True)
    email = db.EmailProperty()
    first_name = db.StringProperty()
    last_name = db.StringProperty()

    class Meta:
        abstract = True
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @classmethod
    def create_djangouser_for_user(cls, user):
        return cls(user=user, email=user.email(), username=user.email())
