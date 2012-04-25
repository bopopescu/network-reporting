from google.appengine.ext import db
from django.contrib.auth.models import *
from django.utils.translation import ugettext_lazy as _

class UserTraits(db.Model):
    last_login = db.DateTimeProperty()
    date_joined = db.DateTimeProperty(auto_now_add=True)
    is_active = db.BooleanProperty(default=True)
    is_staff = db.BooleanProperty(default=False)
    is_superuser = db.BooleanProperty(default=False)
    password = db.StringProperty(default=UNUSABLE_PASSWORD)
    # groups = KeyListProperty(Group, verbose_name=_('groups'))
    # user_permissions = FakeModelListProperty(Permission,
    #     verbose_name=_('user permissions'))

    objects = UserManager()

    class Meta:
        abstract = True

    def is_anonymous(self):
        "Always returns False. This is a way of comparing User objects to anonymous users."
        return False

    def is_authenticated(self):
        """Always return True. This is a way to tell if the user has been authenticated in templates.
        """
        return True

    def get_full_name(self):
        "Returns the first_name plus the last_name, with a space in between."
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        encryption formats behind the scenes.
        """
        # Backwards-compatibility check. Older passwords won't include the
        # algorithm or salt.
        if '$' not in self.password:
            is_correct = (self.password == get_hexdigest('md5', '', raw_password))
            if is_correct:
                # Convert the password to the new, more secure format.
                self.set_password(raw_password)
                self.save()
            return is_correct
        # Backwards-compatibility check for old app-engine-patch hash format
        if self.password.split('$')[0] == 'sha512':
            valid = check_password(raw_password, self.password)
            if valid:
                self.set_password(raw_password)
                self.save()
            return valid
        return check_password(raw_password, self.password)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = UNUSABLE_PASSWORD

    def has_usable_password(self):
        return self.password != UNUSABLE_PASSWORD

    def get_group_permissions(self):
        """
        Returns a list of permission strings that this user has through
        his/her groups. This method queries all available auth backends.
        """
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                permissions.update(backend.get_group_permissions(self))
        return permissions

    def get_all_permissions(self):
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_all_permissions"):
                permissions.update(backend.get_all_permissions(self))
        return permissions

    def has_perm(self, perm):
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general.
        """
        # Inactive users have no permissions.
        if not self.is_active:
            return False

        # Superusers have all permissions.
        if self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        for backend in auth.get_backends():
            if hasattr(backend, "has_perm"):
                if backend.has_perm(self, perm):
                    return True
        return False

    def has_perms(self, perm_list):
        """Returns True if the user has each of the specified permissions."""
        for perm in perm_list:
            if not self.has_perm(perm):
                return False
        return True

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app
        label. Uses pretty much the same logic as has_perm, above.
        """
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        for backend in auth.get_backends():
            if hasattr(backend, "has_module_perms"):
                if backend.has_module_perms(self, app_label):
                    return True
        return False

    def get_and_delete_messages(self):
        messages = []
        for m in self.message_set:
            messages.append(m.message)
            m.delete()
        return messages

    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        if not hasattr(self, '_profile_cache'):
            from django.conf import settings
            if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
                raise SiteProfileNotAvailable
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
                model = models.get_model(app_label, model_name)
                self._profile_cache = model.all().filter('user =', self).get()
                if self._profile_cache:
                    self._profile_cache.user = self
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache

class EmailUserTraits(UserTraits):
    def email_user(self, subject, message, from_email=None):
        """Sends an e-mail to this user."""
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email])

    class Meta:
        abstract = True

    def __unicode__(self):
        return unicode(self.email)

class EmailUser(EmailUserTraits):
    email = db.EmailProperty(required=True)
    # This can be used to distinguish between banned users and unfinished
    # registrations
    is_banned = db.BooleanProperty(default=False)
    class Meta:
        abstract = True
