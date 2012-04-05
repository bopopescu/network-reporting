"""
Views which allow users to create and activate accounts.

"""

import logging

from google.appengine.api import mail
from google.appengine.api import urlfetch
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

import urllib

from registration.forms import RegistrationForm, MPRegistrationForm, MPGoogleRegistrationForm, ChangeSettingsForm
from registration.models import RegistrationProfile

from common.ragendja.auth.decorators import google_login_required

def activate(request, activation_key,
             template_name='registration/activate.html',
             extra_context=None):
    """
    Activate a ``User``'s account from an activation key, if their key
    is valid and hasn't expired.

    By default, use the template ``registration/activate.html``; to
    change this, pass the name of a template as the keyword argument
    ``template_name``.

    **Required arguments**

    ``activation_key``
       The activation key to validate and use for activating the
       ``User``.

    **Optional arguments**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``template_name``
        A custom template to use.

    **Context:**

    ``account``
        The ``User`` object corresponding to the account, if the
        activation was successful. ``False`` if the activation was not
        successful.

    ``expiration_days``
        The number of days for which activation keys stay valid after
        registration.

    Any extra variables supplied in the ``extra_context`` argument
    (see above).

    **Template:**

    registration/activate.html or ``template_name`` keyword argument.

    """
    activation_key = activation_key.lower() # Normalize before trying anything with it.
    account = RegistrationProfile.objects.activate_user(activation_key)
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(template_name,
                              { 'account': account,
                                'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS },
                              context_instance=context)

def register(request,
             success_url=None,
             form_class=MPRegistrationForm,
             template_name='registration/registration_form.html',
             extra_context=None,
             auto_login=True,
             account_already_exists=False):
    """
    Allow a new user to register an account.

    Following successful registration, issue a redirect; by default,
    this will be whatever URL corresponds to the named URL pattern
    ``registration_complete``, which will be
    ``/accounts/register/complete/`` if using the included URLConf. To
    change this, point that named pattern at another URL, or pass your
    preferred URL as the keyword argument ``success_url``.

    By default, ``registration.forms.RegistrationForm`` will be used
    as the registration form; to change this, pass a different form
    class as the ``form_class`` keyword argument. The form class you
    specify must have a method ``save`` which will create and return
    the new ``User``.

    By default, use the template
    ``registration/registration_form.html``; to change this, pass the
    name of a template as the keyword argument ``template_name``.

    **Required arguments**

    None.

    **Optional arguments**

    ``form_class``
        The form class to use for registration.

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``success_url``
        The URL to redirect to on successful registration.

    ``template_name``
        A custom template to use.

    **Context:**

    ``form``
        The registration form.

    Any extra variables supplied in the ``extra_context`` argument
    (see above).

    **Template:**

    registration/registration_form.html or ``template_name`` keyword
    argument.

    """
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES, request=request)
        domain_override = request.get_host()

        # Check reCAPTCHA response
        captcha_success, form.captcha_error_msg = verify_captcha(request)

        if form.is_valid() and (captcha_success or account_already_exists):
            new_user = form.save(domain_override)

            # Send welcome email
            if not account_already_exists:
                try:
                    mail.send_mail(sender="MoPub, Inc. <olp@mopub.com>",
                                   reply_to="support@mopub.com",
                                   to=new_user.email,
                                   subject="Welcome to MoPub!",
                                   body="""
Hi %s,
Welcome to MoPub, the easiest way to turn your apps into businesses.  Now you can optimize your mobile ad network relationships or easily serve direct-sold ads into your mobile apps -- all through a simple, open-source client library.

Get started here:
http://app.mopub.com/

Questions?  Email support@mopub.com or check out our Help FAQ at http://help.mopub.com/ (yes, it's actually helpful).

Thanks!
The MoPub Team"""%(new_user.first_name))
                except:
                    pass

            # success_url needs to be dynamically generated here; setting a
            # a default value using reverse() will cause circular-import
            # problems with the default URLConf for this application, which
            # imports this file.
            if auto_login:
                login_user = authenticate(username=form.cleaned_data['email'],
                                          password=form.cleaned_data['password1'])
                auth_login(request, login_user)
            return HttpResponseRedirect(success_url or reverse('publisher_create_app')+'?reg_complete=1')
    else:
        form = form_class(request=request)

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(template_name,
                              { 'form': form },
                              context_instance=context)

def verify_captcha(request):
        # Ping the reCAPTCHA API from the account submit form
        # Returns a tuple: (boolean success, string error)
        #
        # Notes:
        # Successful response from reCAPTCHA API will be a single line:
        #   true
        # Unsuccessful response from reCAPTCHA API will be two lines:
        #   false
        #   <error_code>
        #
        # The errors are: invalid-site-private-key, invalid-request-cookie,
        # incorrect-captcha-sol and recaptcha-not-reachable.  These should be included
        # in the redisplay as &error=incorrect-captcha-sol, for example
        #
        captcha_url = 'http://www.google.com/recaptcha/api/verify'
        captcha_private_key = '6LcbPcsSAAAAADQSC_Z6ZKaMqfQx_iNDDsVTWOcU'

        captcha_data = {
            'remoteip': request.META.get('REMOTE_ADDR'),
            'privatekey': captcha_private_key,
            'challenge': request.POST.get('recaptcha_challenge_field'),
            'response': request.POST.get('recaptcha_response_field')
        }

        try:
            response = urlfetch.fetch(captcha_url,
                method=urlfetch.POST,
                payload=urllib.urlencode(captcha_data),
                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        except:
            return (False, None)

        if response.status_code == 200:
            try:
                lines = response.content.splitlines()
                if lines[0] == 'true':
                    return (True, None)
                else:
                    return (False, lines[1])
            except:
                pass

        return (False, None)

@login_required
def settings_change(request,
                    success_url=None,
                    form_class=ChangeSettingsForm,
                    template_name='registration/settings_change_form.html',
                    success_banner=False):

    return register(request,
                    success_url=reverse('settings_change_success'),
                    form_class=form_class,
                    template_name=template_name,
                    extra_context={'success_banner':success_banner},
                    auto_login=False,
                    account_already_exists=True)

@login_required
def settings_change_success(request):

    return settings_change( request,
                            success_url=None,
                            form_class=ChangeSettingsForm,
                            template_name='registration/settings_change_form.html',
                            success_banner=True)

@google_login_required
def register_google(request,
                        success_url=None,
                        form_class=MPGoogleRegistrationForm,
                        template_name='registration/registration_google_form.html',
                        extra_context=None):
    return register(request,
                    success_url=success_url,
                    form_class=form_class,
                    template_name=template_name,
                    extra_context=None,
                    auto_login=False)
