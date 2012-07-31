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
            'singular': False,
        }
    else:
        return {
            'inventory': [inventory],
            'singular': True,
        }


@register.inclusion_tag("common/partials/app_row.html")
def app_row(app, singular=False):
    return {
        'app': app,
        'singular': singular,
    }


@register.inclusion_tag("common/partials/adunit_row.html")
def adunit_row(adunit, include_icon_placeholder=True):
    return {
        'adunit': adunit,
        'include_icon_placeholder': include_icon_placeholder
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


@register.inclusion_tag("common/partials/line_item_table.html")
def line_item_table(line_items):
    """
    Renders an line_item or a group of line_items in a table.
    If include_targeting is true, it'll include
    """

    # If the object isn't iterable (for instance, a single line_item), put
    # it in a list so that we can iterate over it in the template
    if not isiterable(line_items):
        line_items = [line_items]

    return {
        'line_items': line_items,
    }


@register.inclusion_tag("common/partials/order_row.html")
def order_row(order):
    return {
        'order': order,
    }


@register.inclusion_tag("common/partials/line_item_row.html")
def line_item_row(line_item):
    return {
        'line_item': line_item,
    }


@register.inclusion_tag("common/partials/network_campaign_row.html")
def network_campaign_row(network_campaign):
    return {
        'network_campaign': network_campaign,
    }


@register.inclusion_tag("common/partials/network_adgroup_row.html")
def network_adgroup_row(network_adgroup):
    return {
        'network_adgroup': network_adgroup,
    }


@register.inclusion_tag("common/partials/marketplace_campaign_row.html")
def marketplace_campaign_row(marketplace_campaign):
    return {
        'marketplace_campaign': marketplace_campaign,
    }


@register.inclusion_tag("common/partials/marketplace_adgroup_row.html")
def marketplace_adgroup_row(marketplace_adgroup):
    return {
        'marketplace_adgroup': marketplace_adgroup,
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

@register.inclusion_tag("common/partials/filter_buttons.html")
def filter_buttons():
    return {}


@register.inclusion_tag("common/partials/status_icon.html")
def status_icon(adgroup):
    """
    Returns an image tag based on the adgroup's status
    (deleted/active/inactive/paused).
    """
    return {'adgroup': adgroup}

@register.inclusion_tag("common/partials/button_icon.html")
def button_icon(name):
    """
    Returns an image tag with a button icon.
    """
    return {'name': name}


@register.inclusion_tag("common/partials/chart_placeholder.html")
def chart_placeholder(start_date, end_date):
    """
    Placeholder for a chart before it loads
    """
    return {
        'start_date': start_date,
        'end_date': end_date,
    }

@register.inclusion_tag("common/partials/targeting_table.html")
def targeting_table(targeted_adgroups):
    return {
        'targeted_adgroups': targeted_adgroups
    }


@register.inclusion_tag("common/partials/line_item_status.html")
def line_item_status(line_item):
    return {
        'line_item': line_item
    }


def isiterable(item):
    try:
        iter(item)
    except TypeError:
        return False
    return True
