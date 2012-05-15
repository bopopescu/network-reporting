from django.template import Context, Library, loader

from advertiser.forms import (NewCreativeForm, ImageCreativeForm,
                              TextAndTileCreativeForm, HtmlCreativeForm)


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


@register.inclusion_tag("common/partials/creative_table.html")
def creative_table(creatives):
    """
    Renders a creative or a group of creatives in a table.
    """
    singular = False

    # If the object isn't iterable (for instance, a single creative), put
    # it in a list so that we can iterate over it in the template
    if not isiterable(creatives):
        singular = True
        creatives = [creatives]

    return {
        'creatives': creatives,
        'singular': singular,
    }


@register.inclusion_tag("common/partials/creative_row.html")
def creative_row(creative):
    return {
        'creative': creative,
    }


@register.simple_tag
def creative_form(creative=None):
    if creative:
        context = {
            'creative': creative,
        }
        if creative.ad_type == 'image':
            context['creative_form'] = ImageCreativeForm(instance=creative)
        elif creative.ad_type == 'text_icon':
            context['creative_form'] = TextAndTileCreativeForm(instance=creative)
        elif creative.ad_type == 'html':
            context['creative_form'] = HtmlCreativeForm(instance=creative)
        else:
            return ""
    else:
        context = {
            'creative_form': NewCreativeForm(),
        }

    template = loader.get_template('advertiser/forms/creative_form.html')
    return template.render(Context(context))


@register.inclusion_tag("advertiser/creative_preview.html")
def creative_preview(creative):
    return {
        'creative': creative,
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
