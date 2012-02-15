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
    return {'inventory': inventory}


@register.inclusion_tag("partials/stats_breakdown.html")
def stats_breakdown(stats):
    return {'stats': stats }


@register.inclusion_tag("partials/status_icon.html")
def status_icon(adgroup):
    """
    Returns an image tag based on the adgroup's status
    (deleted/active/inactive/paused).
    """
    return {'adgroup': adgroup }