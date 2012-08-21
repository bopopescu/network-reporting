from django.template import Library

register = Library()

@register.inclusion_tag("networks/partials/revenue_reporting_form.html")
def revenue_reporting_form(network, reporting):
    return {
        'network': network,
        'reporting': reporting
    }