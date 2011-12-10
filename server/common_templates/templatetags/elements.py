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
