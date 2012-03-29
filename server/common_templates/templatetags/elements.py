from django.template import NodeList, \
     Template, \
     Context, \
     Variable, \
     Library, \
     Node, \
     loader, \
     TemplateSyntaxError, \
     VariableDoesNotExist

register = Library()

@register.inclusion_tag("partials/inventory_table.html")
def inventory_table(inventory):
    # If the object isn't iterable (for instance, a single app), put
    # it in a list so that we can iterate over it in the template
    if isiterable(inventory):
        return {
            'inventory': inventory,
            'singular': False
        }
    else:
        return {
            'inventory': [inventory],
            'singular': True
        }


@register.inclusion_tag("partials/stats_breakdown.html")
def stats_breakdown(stats):
    return {'stats': stats }


@register.inclusion_tag("partials/status_icon.html")
def status_icon(advertiser_model):
    """
    Returns an image tag based on the adgroup's status
    (deleted/active/inactive/paused).
    """
    return {'adgroup': advertiser_model }


def isiterable(item):
    try:
        item_iterater = iter(item)
    except TypeError:
        return False
    return True
