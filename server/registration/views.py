"""
Views which allow users to create and activate accounts.

"""

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext


from registration.forms import RegistrationForm, MPRegistrationForm, MPGoogleRegistrationForm
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

def register(request, success_url=None,
             form_class=MPRegistrationForm,
             template_name='registration/registration_form.html',
             extra_context=None, auto_login=True):
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
        if form.is_valid():
            new_user = form.save(domain_override)
            # success_url needs to be dynamically generated here; setting a
            # a default value using reverse() will cause circular-import
            # problems with the default URLConf for this application, which
            # imports this file.
            if auto_login:
                login_user = authenticate(username=form.cleaned_data['email'],
                                          password=form.cleaned_data['password1'])
                auth_login(request, login_user)
            return HttpResponseRedirect(success_url or reverse('publisher_app_create')+'?reg_complete=1')
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