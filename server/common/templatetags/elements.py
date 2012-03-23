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
def order_table(orders, show_status=True):
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
        'show_status': show_status,
    }

    
@register.inclusion_tag("common/partials/order_row.html")
def order_row(order, show_status=True):
    return {
        'order': order,
        'show_status': show_status,
    }


@register.inclusion_tag("common/partials/line_item_table.html")
def line_item_table(line_items, show_status=True):
    """
    Renders an line_item or a group of line_items in a table.
    If include_targeting is true, it'll include
    """
    singular = False

    # If the object isn't iterable (for instance, a single line_item), put
    # it in a list so that we can iterate over it in the template
    if not isiterable(line_items):
        singular = True
        line_items = [line_items]
        
    return {
        'line_items': line_items,
        'singular': singular,
        'show_status': show_status
    }

    
    
@register.inclusion_tag("common/partials/line_item_row.html")
def line_item_row(line_item, show_status=False):
    return {
        'line_item': line_item,
        'show_status': show_status
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
