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
    return {'stats': stats } #redundo