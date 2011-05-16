"""
Forms and validation code for user registration.

"""

from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _

from registration.models import RegistrationProfile


# I put this on all required fields, because it's easier to pick up
# on them with CSS or JavaScript if they have a class of "required"
# in the HTML. Your mileage may vary. If/when Django ticket #3515
# lands in trunk, this will no longer be necessary.
attrs_dict = { 'class': 'required' }

from common.constants import (ISO_COUNTRIES, US_STATES)
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from account.models import Account#, User
from account.query_managers import UserQueryManager,AccountQueryManager


class BaseRegistrationForm(mpforms.MPForm):
    TEMPLATE = 'registration/forms/registration_form.html'
    
    first_name = mpfields.MPTextField()
    last_name = mpfields.MPTextField()
    title = mpfields.MPTextField(required=False)
    company = mpfields.MPTextField()
    phone = mpfields.MPTextField(required=False) # TODO: make phone number property
    country = mpfields.MPChoiceField(choices=ISO_COUNTRIES,widget=mpwidgets.MPSelectWidget)
    traffic = forms.TypedChoiceField(choices=[("0","Haven't launched yet"),
                                              ("1","1-10MM"),
                                              ("10","10-90MM"),
                                              ("100","90-200MM"),
                                              ("200","200MM+")],
                                     widget=mpwidgets.MPSelectWidget,
                                     coerce=float)
    
    mailing_list = forms.BooleanField(label=_(u'I would like to receive occasion product update emails from MoPub'),
                                      initial=True,
                                      required=False)
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs=attrs_dict),
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={ 'required': u"Please accept the terms and conditions in order to start using MoPub" })
    
    
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request',None)
        super(BaseRegistrationForm, self).__init__(*args, **kwargs)
    
    
    def clean_email(self):
        """
        Validate that the email is not already
        in use.
        
        """
        model = User
        user = UserQueryManager.get_by_email(self.cleaned_data['email'].lower())
        if user:
            raise forms.ValidationError(_(u'This email already has an account.'))
        return self.cleaned_data['email']
        

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_(u'Please enter the same password for each time.'))
        return self.cleaned_data
    
    def save(self, domain_override=""):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User`` (by calling
        ``RegistrationProfile.objects.create_inactive_user()``).
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(**self.cleaned_data)
        return new_user
    

class MPGoogleRegistrationForm(BaseRegistrationForm):
    def save(self, domain_override=""):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User`` (by calling
        ``RegistrationProfile.objects.create_inactive_user()``).
        
        """
        self.cleaned_data.update(username=self.request.user.username)
        new_user = self.request.user
        
        def _get_model_params(Model):
            # get property names of the stats model
            properties = Model.properties() # passes back dictionary with key = property names
            properties = [k for k in properties]

            # pull out the appropriate values from the input arguments
            d = {}
            for p in properties:
                value = self.cleaned_data.get(p,None)
                if value:
                    d[p] = value
            return d
        
        user_details = _get_model_params(User)
        for prop_name,value in user_details.iteritems():
            setattr(new_user,prop_name,value)
        new_user.put()
        
        # create new account for this user as well        
        account_details = _get_model_params(Account)
        account = AccountQueryManager.get_current_account(user=new_user)
        for prop_name,value in account_details.iteritems():
            setattr(account,prop_name,value)
        account.put()
        return new_user
        
class MPUserAccountForm(BaseRegistrationForm):
    pass        
    

class MPRegistrationForm(BaseRegistrationForm):
    
    
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_(u'email address'))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'password'))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'password (again)'))
    
    def save(self, domain_override=""):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User`` (by calling
        ``RegistrationProfile.objects.create_inactive_user()``).
        
        """
        self.cleaned_data.update(password=self.cleaned_data['password1'])
        self.cleaned_data.update(username=self.cleaned_data['email'])
        new_user = RegistrationProfile.objects.create_active_user(**self.cleaned_data)
        return new_user

class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should either preserve the base ``save()`` or implement
    a ``save()`` method which returns a ``User``.
    
    """
    username = forms.RegexField(regex=r'^\w+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_(u'username'))
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_(u'email address'))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'password'))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'password (again)'))
    
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        user = User.get_by_key_name("key_"+self.cleaned_data['username'].lower())
        if user:
            raise forms.ValidationError(_(u'This username is already taken. Please choose another.'))
        return self.cleaned_data['username']
        

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_(u'You must type the same password each time'))
        return self.cleaned_data
    
    def save(self, domain_override=""):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User`` (by calling
        ``RegistrationProfile.objects.create_inactive_user()``).
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(username=self.cleaned_data['username'],
                                                                    password=self.cleaned_data['password1'],
                                                                    email=self.cleaned_data['email'],
                                                                    domain_override=domain_override,
                                                                    )
        return new_user


class RegistrationFormTermsOfService(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service.
    
    """
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs=attrs_dict),
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={ 'required': u"You must agree to the terms to register" })


class RegistrationFormUniqueEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.
    
    """
    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.
        
        """
        email = self.cleaned_data['email'].lower()
        if User.all().filter('email =', email).count(1):
            raise forms.ValidationError(_(u'This email address is already in use. Please supply a different email address.'))
        return email


class RegistrationFormNoFreeEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration with
    email addresses from popular free webmail services; moderately
    useful for preventing automated spam registrations.
    
    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.
    
    """
    bad_domains = ['aim.com', 'aol.com', 'email.com', 'gmail.com',
                   'googlemail.com', 'hotmail.com', 'hushmail.com',
                   'msn.com', 'mail.ru', 'mailinator.com', 'live.com']
    
    def clean_email(self):
        """
        Check the supplied email address against a list of known free
        webmail domains.
        
        """
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise forms.ValidationError(_(u'Registration using free email addresses is prohibited. Please supply a different email address.'))
        return self.cleaned_data['email']
