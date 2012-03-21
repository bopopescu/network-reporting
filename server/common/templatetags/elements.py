from django.template import Library

register = Library()


@register.inclusion_tag("common/partials/inventory_table.html")
def inventory_table(inventory, include_targeting=False):
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


@register.inclusion_tag("common/partials/order_table.html")
def order_table(orders, include_status=False):
    """
    Renders an order or a group of orders in a table.
    If include_targeting is true, it'll include
    """
    
    singular = False

    # If the object isn't iterable (for instance, a single order), put
    # it in a list so that we can iterate over it in the template
    if not isiterable(orders):
        singular = True
        orders = [orders]
        
    return {
        'orders': orders,
        'singular': singular,
        'include_status': include_status,
    }


@register.inclusion_tag("common/partials/stats_breakdown.html")
def stats_breakdown(stats):
    return {'stats': stats}


@register.inclusion_tag("common/partials/status_icon.html")
def status_icon(adgroup):
    """
    Returns an image tag based on the adgroup's status
    (deleted/active/inactive/paused).
    """
    return {'adgroup': adgroup}

def isiterable(item):
    try:
        iter(item)
    except TypeError:
        return False
    return True
