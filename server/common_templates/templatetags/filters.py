import re
import time
from datetime import datetime
from django import template
import binascii
from django.utils import simplejson as json
import logging
import string
from common.utils.tzinfo import Pacific, utc

from django.conf import settings
from django.core.urlresolvers import reverse

from country_codes import COUNTRY_CODE_DICT

register = template.Library()

numeric_test = re.compile("^\d+$")

@register.filter
def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'has_key') and value.has_key(arg):
        return value[arg]
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return settings.TEMPLATE_STRING_IF_INVALID

class_re = re.compile(r'(?<=class=["\'])(.*)(?=["\'])')
@register.filter
def add_class(value, css_class):
    string = unicode(value)
    match = class_re.search(string)
    if match:
        m = re.search(r'^%s$|^%s\s|\s%s\s|\s%s$' % (css_class, css_class,
            css_class, css_class), match.group(1))
        print match.group(1)
        if not m:
            return mark_safe(class_re.sub(match.group(1) + " " + css_class,
                string))
        else:
            return mark_safe(string.replace('>', ' class="%s">' % css_class))
        return value

@register.filter
def attrs(bound_field, attrs_json):
    """
    Parses a json attrs object from template and passes them to the bound_field
    """
    parsed = json.loads(attrs_json)
    bound_field.add_attrs(attrs=parsed)
    return bound_field

@register.filter
def raw(bound_field):
    """
    Parses a json attrs object from template and passes them to the bound_field
    """
    bound_field.TEMPLATE = 'raw_bound_field.html'
    return bound_field

@register.filter
def raw_required(bound_field):
    """
    Parses a json attrs object from template and passes them to the bound_field
    """
    bound_field.TEMPLATE = 'raw_bound_field_required.html'
    return bound_field

@register.filter
def raw_required_with_errors(bound_field):
    bound_field.TEMPLATE = 'raw_bound_field_required_with_errors.html'
    return bound_field

@register.filter
def widget_only(bound_field):
    bound_field.TEMPLATE = 'widget_only.html'
    return bound_field


@register.filter
def label(bound_field, label):
    """
    Sets the label of a field
    """
    bound_field.add_label(label)
    return bound_field

@register.filter
def kmbt(value):
    if value:
        value = withsep(int(value))
        endings = ['K', 'M', 'B', 'T', 'Q']
        parts = value.split(',')
        if 1 < len(parts) < 7 :
            return parts[0] + endings[len(parts)-2]
        elif len(parts) >= 7:
            return value
        else:
            return parts[0]
    else:
        return "0"

@register.filter
def currency(value):
    if value:
        try:
            value = round(value, 2)
            return "$%s%s" % (withsep(int(value)), ("%0.2f" % value)[-3:])
        except Exception:
            return "$0.00"
    else:
        return "$0.00"

@register.filter
def currency_no_symbol(value):
    if value:
        try:
            return "---" # "%s%s" % (withsep(int(value)), ("%0.2f" % value)[-3:])
        except Exception:
            return "---" # "0.00"
    else:
        return "---" # "0.00"

@register.filter
def percentage(value):
    if value:
        try:
            return "%1.2f%%" % ((value or 0) * 100)
        except Exception:
            return "0.00%"
    else:
        return "0.00%"

@register.filter
def percentage_rounded(value):
    if value:
        try:
            return "%1.0f%%" % ((value or 0) * 100)
        except Exception:
            return "0%"
    else:
        return "0%"


@register.filter
def upper(s):
    return string.upper(s)


@register.filter
def withsep(value):
    """ 1000000 --> 1,000,000 """
    if value:
        try:
            match = re.sub(r'(\d{3})(?=\d)', r'\1,', str(value)[::-1])[::-1]
            if match:
                return match
            return "0"
        except Exception:
            return "0"
    else:
        return "0"

@register.filter
def format_date(value):
    if value:
        try:
            return value.strftime("%a, %b %d, %Y")
        except Exception:
            return ""
    else:
        return ""

@register.filter
def format_date_compact(value):
    if value:
        try:
            return "%d/%d" % (value.month, value.day)
        except Exception:
            return ""
    else:
        return ""

@register.filter
def format_date_time(value):
    if value:
        try:
            return value.replace(tzinfo=utc).astimezone(Pacific).strftime("%m/%d/%Y %I:%M %p")
        except Exception:
            return ""
    else:
        return ""

@register.filter
def format_time(value):
    if value:
        try:
            return value.strftime("%I:%M %p")
        except Exception:
            return ""
    else:
        return ""

@register.filter
def format_utc_date_compact(value):
    value = value.replace(tzinfo=utc).astimezone(Pacific)
    return "%d/%d" % (value.month, value.day)

@register.filter
def truncate(value, arg):
    if len(value) > arg:
        try:
            return "%s..." % value[:(arg-3)]
        except Exception:
            return value
    else:
        return value

@register.filter
def time_ago_in_words(value):
    if value:
        if type(value) == str or type(value) == unicode:
            value = datetime(*time.strptime(value, "%a %b %d %H:%M:%S +0000 %Y")[0:5])

        d = datetime.now() - value
        if d.days < 1:
            if d.seconds < 60:
                return "less than a minute"
            elif d.seconds < 120:
                return "about a minute"
            elif d.seconds < (60 * 60):
                return "%d minutes" % (d.seconds / 60)
            elif d.seconds < (2 * 60 * 60):
                return "about an hour"
            elif d.seconds < (24 * 60 * 60):
                return "%d hours" % (d.seconds / 60 / 60)
            elif d.days < 2:
                return "one day"
            else:
                return "%d days" % (d.days)

@register.filter
def campaign_status(adgroup):
    d = datetime.now().date()
    campaign = adgroup.campaign
    if (campaign.start_date is None or d >= campaign.start_date) \
       and (campaign.end_date is None or d <= campaign.end_date):
        if not adgroup.active:
            return "Paused"
        if adgroup.campaign.budget:
            if adgroup.percent_delivered and adgroup.percent_delivered < 100.0:
                return "Running"
            elif adgroup.percent_delivered and adgroup.percent_delivered >= 100.0:
                return "Completed"
            else:
                # Eligible campaigns have 0% delivery.
                # In production, they should only last a couple seconds
                # before becoming running campaigns
                return "Eligible"
        else:
            return "Running"
    elif campaign.end_date and d > campaign.end_date:
        return "Completed"
    elif campaign.start_date and d < campaign.start_date:
        return "Scheduled"
    else:
        return "Unknown"

@register.filter
def binary_data(data):
    if data:
        return "data:image/png;base64,%s" % binascii.b2a_base64(data)
    return None

@register.filter
def country_code_to_name(country_code):
    if country_code in COUNTRY_CODE_DICT:
        return COUNTRY_CODE_DICT.get(country_code)
    else:
        logging.warning("No country name for code: %s"%country_code)
        return None

@register.filter
def to_json(python_obj):
    return json.dumps(python_obj)

@register.filter
def as_list(item):
    if type(item) == list:
        return item
    return [item]


@register.filter
def adgroup_to_json(adgroup):
    data = {}
    if adgroup:
        data.update({
            'id': str(adgroup.key()),
            'active': adgroup.active,
            'name': adgroup.name,
            'details_url': reverse('advertiser_adgroup_show', kwargs={'adgroup_key': str(adgroup.key())}),
            'bid_strategy': adgroup.bid_strategy,
            'status': adgroup.status,
        })
        if adgroup.campaign.gtee() or adgroup.campaign.promo():
            start_datetime = adgroup.campaign.start_datetime.replace(tzinfo=utc).astimezone(Pacific) if adgroup.campaign.start_datetime else None
            end_datetime = adgroup.campaign.end_datetime.replace(tzinfo=utc).astimezone(Pacific) if adgroup.campaign.end_datetime else None
            data.update({
                'start_date': "%d/%d" % (start_datetime.month, start_datetime.day) if start_datetime else None,
                'end_date': "%d/%d" % (end_datetime.month, end_datetime.day) if end_datetime else None,
                'apps': [str(key) for key in adgroup.targeted_app_keys],
            })
        if adgroup.campaign.gtee():
            data.update({
                'level': 'high' if adgroup.campaign.campaign_type == 'gtee_high' else 'normal' if adgroup.campaign.campaign_type == 'gtee' else 'low',
                'budget_type': adgroup.campaign.budget_type,
                'budget': adgroup.campaign.budget if adgroup.campaign.budget_type == "daily" else adgroup.campaign.full_budget,
                'goal': adgroup.budget_goal,
            })
        if adgroup.campaign.network():
            data.update({
                'network_type': adgroup.network_type,
            })
    return json.dumps(data)


# Inclusion tags

@register.simple_tag
def include_raw(path):
    """
    Includes raw file data from `path`. This is useful for loading
    javascript templates (such as mustache.js templates) that would
    normally be interpolated with the template context.
    """
    return template.loader.find_template(path)[0]

# @register.simple_tag
# def include_script(script_name,
#                    load_minified=(not settings.DEBUG),
#                    overload=settings.DEBUG):
#     """
#     Includes a script tag (should be a js file) and considers whether
#     the script should be loaded (if we're in production, only load the
#     'app' file, otherwise overload), and what the version number should
#     be (whatever is in settings.py if we're in production, otherwise a
#     random number to bust the cache). Just pass in the name, such as
#     'controllers/networks', don't bother with the '.js'.
#     """
#     # clean up the script name
#     script_name = script_name.replace(".min.js", "")
#     script_name = script_name.replace(".js", "")

#     # make the script path
#     path_prefix = "/js/"

#     if load_minified:
#         path_suffix = ".min.js"
#     else:
#         path_suffix = ".js"

#     if overload:
#         version_number = "?=%s" % str(time.time()).split('.')[0]
#     else:
#         version_number = "?=%s" % str(settings.STATIC_VERSION_NUMBER)

#     script_path = path_prefix + script_name + path_suffix + version_number

#     if script_name == 'app' or overload:
#         return """<script type="text/javascript" src="%s"></script>""" % script_path
#     else:
#         return ""

@register.simple_tag
def include_script(script_name,
                   load_minified=(not settings.DEBUG),
                   overload=settings.DEBUG):

    # clean up the script name
    script_name = script_name.replace(".min.js", "")
    script_name = script_name.replace(".js", "")

    # make the script path
    path_prefix = "/js/"
    path_suffix = ".js"
    version_number = "?=%s" % str(settings.SCRIPTS_VERSION_NUMBER)

    script_path = path_prefix + script_name + path_suffix + version_number

    if not script_name == 'app':
        return """<script type="text/javascript" src="%s"></script>""" % script_path
    else:
        return ""

@register.simple_tag
def include_style(style_name):
    style_name = style_name.replace('.css', '')
    path_prefix = "/css/"
    path_suffix = ".css"
    version_number = "?=%s" % str(settings.STYLES_VERSION_NUMBER)

    style_path = path_prefix + style_name + path_suffix + version_number

    return """<link rel="stylesheet" href="%s" />""" % style_path

@register.filter
def js_date(date):
    return "new Date(%s,%s,%s)" % (date.year, date.month-1, date.day)
