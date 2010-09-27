from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings


def whitelist_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in
    and is on the whitelist, redirecting
    to the log-in page if necessary.
    """    
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.email in settings.WHITELIST_EMAILS,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
