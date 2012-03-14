# Hack Nafis: override the auth forms if we want
from django.conf import settings
from django.contrib.auth.forms import *
from django.contrib.auth import forms as django_forms

from django.utils.translation import ugettext_lazy as _

from account.query_managers import UserQueryManager



class PasswordResetForm(django_forms.PasswordResetForm):
    # email = forms.EmailField(label=_("E-mail"), max_length=75)
    class UserError(Exception):
        pass


    def clean_email(self):
        """
        Validates that a user exists with the given e-mail address.
        """
        email = self.cleaned_data["email"]
        self.users_cache = UserQueryManager.get_by_email(email)
        if not self.users_cache:
            raise forms.ValidationError(_("We couldn't find this email in our system. Are you sure you've registered?"))

        # if its a google user and doesn't have a password
        # then we know that this account is only for google authentication
        import logging
        logging.info("%s %s"%(self.users_cache.user,self.users_cache.has_usable_password()))
        if self.users_cache.user and not self.users_cache.has_usable_password():
            raise AttributeError('Google User Error')

        self.users_cache = [self.users_cache]
        return email

    def save(self, domain_override=None, email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator, request=None):
        """
        Generates a one-use only link for resetting password and sends to the user
        """
        from django.core.mail import send_mail, EmailMessage
        for user in self.users_cache:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            site_name = 'MoPub'
            t = loader.get_template(email_template_name)
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': user.id,
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            email = EmailMessage(_("Password reset on %s") % site_name,
                                t.render(Context(c)),
                                settings.DEFAULT_FROM_EMAIL,
                                [user.email],
                                headers={'Reply-To': settings.REPLY_TO_EMAIL}
                                )
            email.send()
