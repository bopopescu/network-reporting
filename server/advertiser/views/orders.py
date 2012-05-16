__doc__ = """
Views for orders and line items.

'Order' is an alias for 'Campaign', and 'LineItem' is an alias for
'AdGroup'.  We decided to make this change because many other
advertisers use this language.  The code hasn't adopted this naming
convention, and instead still uses "Campaign" and "AdGroup" for
compatibility with the ad server.

Whenever you see "Campaign", think "Order", and wherever you see
"AdGroup", think "LineItem".
"""

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404

from common.utils import helpers
from common.ragendja.template import render_to_response, JSONResponse
from common.utils.request_handler import RequestHandler

from account.query_managers import AccountQueryManager
from advertiser.forms import (OrderForm, LineItemForm, NewCreativeForm,
                              ImageCreativeForm, TextAndTileCreativeForm,
                              HtmlCreativeForm)
from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)
from publisher.query_managers import AppQueryManager, AdUnitQueryManager
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

import logging


flatten = lambda l: [item for sublist in l for item in sublist]

ctr = lambda clicks, impressions: \
      (clicks / float(impressions) if impressions else 0)


class OrderIndexHandler(RequestHandler):
    """
    Shows a list of orders and line items.
    Orders show:
      - name, status, advertiser, and a top-level stats rollup.
    Line Items show:
      - name, dates, budgeting information, top-level stats.
    """
    def get(self):

        orders = CampaignQueryManager.get_order_campaigns(account=self.account)
        line_items = AdGroupQueryManager.get_adgroups(account=self.account)
        line_items = [l for l in line_items if not (l.campaign.advertiser == "marketplace")]
        for line_item in line_items:
            logging.warn(line_item.budget_goal_display)

        return {
            'orders': orders,
            'line_items': line_items
        }


@login_required
def order_index(request, *args, **kwargs):
    t = "advertiser/order_index.html"
    return OrderIndexHandler(template=t)(request, use_cache=False, *args, **kwargs)


class OrderDetailHandler(RequestHandler):
    """
    Top level stats rollup for all of the line items within the order.
    Lists each line item within the order with links to line item details.
    """
    def get(self, order_key):

        # Grab the campaign info
        order = CampaignQueryManager.get(order_key)

        # Set up the stats
        stats_q = StatsModelQueryManager(self.account, self.offline)
        all_stats = stats_q.get_stats_for_days(advertiser=order, days=self.days)

        # Get the targeted adunits and group them by their app.
        targeted_adunits = set(flatten([AdUnitQueryManager.get(line_item.site_keys) \
                                    for line_item in order.adgroups]))
        targeted_apps = get_targeted_apps(targeted_adunits)

        # Set up the form
        order_form = OrderForm(instance=order)

        return {
            'order': order,
            'order_form': order_form,
            'stats': format_stats(all_stats),
            'targeted_apps': targeted_apps.values(),
            'targeted_app_keys': targeted_apps.keys(),
            'targeted_adunits': targeted_adunits
        }


@login_required
def order_detail(request, *args, **kwargs):
    handler = OrderDetailHandler(template="advertiser/order_detail.html",
                                 id="order_key")
    return handler(request, use_cache=False, *args, **kwargs)


class LineItemDetailHandler(RequestHandler):
    """
    Almost identical to current campaigns detail page.
    """
    def get(self, line_item_key):

        line_item = AdGroupQueryManager.get(line_item_key)

        # Create creative forms
        creative_form = NewCreativeForm()

        # Get the stats for the date range
        stats_q = StatsModelQueryManager(self.account, self.offline)
        all_stats = stats_q.get_stats_for_days(advertiser=line_item,
                                               days=self.days)
        line_item.stats = reduce(lambda x, y: x + y, all_stats, StatsModel())

        # Get the targeted adunits and apps
        targeted_adunits = AdUnitQueryManager.get(line_item.site_keys)
        targeted_apps = get_targeted_apps(targeted_adunits)

        return {
            'order': line_item.campaign,
            'line_item': line_item,
            'creative_form': creative_form,
            'stats': format_stats(all_stats),
            'targeted_apps': targeted_apps.values(),
            'targeted_app_keys': targeted_apps.keys(),
            'targeted_adunits': targeted_adunits
        }


@login_required
def line_item_detail(request, *args, **kwargs):
    t = "advertiser/lineitem_detail.html"
    return LineItemDetailHandler(template=t, id="line_item_key")(request, use_cache=False, *args, **kwargs)


class AdSourceStatusChangeHandler(RequestHandler):
    """
    Changes the status of a line item or list of line items.
    Author: John Pena
    """
    def post(self):
        # Pull out the params
        ad_sources = self.request.POST.getlist('ad_sources[]')
        status = self.request.POST.get('status', None)

        if ad_sources and status:
            for ad_source_key in ad_sources:
                try:
                    ad_source = CreativeQueryManager.get(ad_source_key)
                    manager_used = CreativeQueryManager
                except:
                    try:
                        ad_source = AdGroupQueryManager.get(ad_source_key)
                        manager_used = AdGroupQueryManager
                    except:
                        ad_source = CampaignQueryManager.get(ad_source_key)
                        manager_used = CampaignQueryManager
                updated = False
                if ad_source.account.key() == self.account.key():
                    if status == 'run' or status == 'play':
                        ad_source.active = True
                        if manager_used != CreativeQueryManager:
                            ad_source.archived = False
                        updated = True
                    elif status == 'pause':
                        ad_source.active = False
                        if manager_used != CreativeQueryManager:
                            ad_source.archived = False
                        updated = True
                    elif status == 'archive':
                        ad_source.active = False
                        if manager_used != CreativeQueryManager:
                            ad_source.archived = True
                        updated = True
                    elif status == 'delete':
                        ad_source.deleted = True
                        ad_source.active = False
                        updated = True

                    if updated:
                        manager_used.put(ad_source)
            return JSONResponse({
                'success': True,
            })

        else:
            return JSONResponse({
                'success': False,
                'errors': 'Bad Parameters'
            })


@login_required
def ad_source_status_change(request, *args, **kwargs):
    return AdSourceStatusChangeHandler()(request, use_cache=False, *args, **kwargs)


class OrderFormHandler(RequestHandler):
    """
    Edit order form handler which gets submitted from the order detail page.
    """
    def post(self, order_key):
        if not self.request.is_ajax():
            raise Http404

        # TODO: make sure this is a gtee or promo order
        instance = CampaignQueryManager.get(order_key)
        order_form = OrderForm(self.request.POST, instance=instance)

        if order_form.is_valid():
            order = order_form.save()
            order.save()
            CampaignQueryManager.put(order)
            # TODO: in js reload instead of looking for redirect
            return JSONResponse({
                'success': True,
            })

        else:
            # TODO: dict comprehension?
            errors = {}
            for key, value in order_form.errors.items():
                # TODO: just join value?
                errors[key] = ' '.join([error for error in value])

            return JSONResponse({
                'errors': errors,
                'success': False,
            })


@login_required
def order_form(request, *args, **kwargs):
    return OrderFormHandler(id="order_key")(request, use_cache=False, *args, **kwargs)


class OrderAndLineItemFormHandler(RequestHandler):
    """
    New/Edit form page for Orders and LineItems.
    """
    def get(self, order_key=None, line_item_key=None):
        if line_item_key:
            line_item = AdGroupQueryManager.get(line_item_key)
            order = line_item.campaign
        elif order_key:
            order = CampaignQueryManager.get(order_key)
            line_item = None
        else:
            order = None
            line_item = None

        if order and not order.is_order:
            raise Http404

        order_form = OrderForm(instance=order, prefix='order')
        line_item_form = LineItemForm(instance=line_item)

        apps = AppQueryManager.get_apps(account=self.account, alphabetize=True)

        return {
            'apps': apps,
            'order': order,
            'order_form': order_form,
            'line_item': line_item,
            'line_item_form': line_item_form,
        }


    def post(self, order_key=None, line_item_key=None):

        if not self.request.is_ajax():
            raise Http404

        if len(self.request.POST.keys()) == 0:
            raise Http404

        if line_item_key:
            line_item = AdGroupQueryManager.get(line_item_key)
            order = line_item.campaign
        elif order_key:
            order = CampaignQueryManager.get(order_key)
            line_item = None
        else:
            order = None
            line_item = None

        if line_item:
            if not line_item.account.key() == self.account.key():
                raise Http404

        if order:
            if (not order.is_order) or order.account.key() != self.account.key():
                raise Http404
        else:
            order_form = OrderForm(self.request.POST, instance=order, prefix='order')

            if order_form.is_valid():
                order = order_form.save()
                order.account = self.account
                order.is_order = True
                order.save()
                CampaignQueryManager.put(order)

            else:
                # TODO: dict comprehension?
                errors = {}
                for key, value in order_form.errors.items():
                    # TODO: just join value?
                    errors[key] = ' '.join([error for error in value])

                return JSONResponse({
                    'errors': errors,
                    'success': False,
                })

        # TODO: do this in the form? maybe pass the account in?
        adunits = AdUnitQueryManager.get_adunits(account=self.account)
        site_keys = [(unicode(adunit.key()), '') for adunit in adunits]
        line_item_form = LineItemForm(self.request.POST, instance=line_item, site_keys=site_keys)

        if line_item_form.is_valid():
            line_item = line_item_form.save()
            line_item.account = self.account
            line_item.campaign = order
            line_item.save()
            AdGroupQueryManager.put(line_item)

            # Onboarding: user is done after they set up their first campaign
            if self.account.status == "step4":
                self.account.status = ""
                AccountQueryManager.put_accounts(self.account)

            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_line_item_detail',
                                    kwargs={'line_item_key': line_item.key()}),
            })

        else:
            errors = {}
            for key, value in line_item_form.errors.items():
                # TODO: find a less hacky way to get jQuery validator's
                # showErrors function to work with the SplitDateTimeWidget
                if key == 'start_datetime':
                    key = 'start_datetime_1'
                elif key == 'end_datetime':
                    key = 'end_datetime_1'
                # TODO: just join value?
                errors[key] = ' '.join([error for error in value])

            return JSONResponse({
                'errors': errors,
                'success': False,
            })


@login_required
def order_and_line_item_form_new_order(request, *args, **kwargs):
    handler = OrderAndLineItemFormHandler(template="advertiser/forms/order_and_line_item_form.html")
    return handler(request, use_cache=False, *args, **kwargs)


@login_required
def order_and_line_item_form_new_line_item(request, *args, **kwargs):
    handler = OrderAndLineItemFormHandler(id="order_key",
                                          template="advertiser/forms/order_and_line_item_form.html")
    return handler(request, use_cache=False, *args, **kwargs)


@login_required
def order_and_line_item_form_edit(request, *args, **kwargs):
    handler = OrderAndLineItemFormHandler(id="line_item_key",
                                          template="advertiser/forms/order_and_line_item_form.html")
    return handler(request, use_cache=False, *args, **kwargs)


class CreativeFormHandler(RequestHandler):
    """
    New/Edit form page for Creatives.
    """
    def post(self, line_item_key=None, creative_key=None):
        if not self.request.is_ajax():
            raise Http404

        if creative_key:
            creative = CreativeQueryManager.get(creative_key)
            line_item = creative.ad_group
        else:
            creative = None
            line_item = AdGroupQueryManager.get(line_item_key)

        ad_type = creative.ad_type if creative else self.request.POST['ad_type']
        if ad_type == 'image':
            creative_form = ImageCreativeForm(self.request.POST,
                                              files=self.request.FILES,
                                              instance=creative)
        elif ad_type == 'text_icon':
            creative_form = TextAndTileCreativeForm(self.request.POST,
                                                    files=self.request.FILES,
                                                    instance=creative)
        elif ad_type == 'html':
            creative_form = HtmlCreativeForm(self.request.POST,
                                             instance=creative)
        else:
            raise Exception("Unsupported creative type %s." % ad_type)  # TODO: real exception type

        if creative_form.is_valid():
            creative = creative_form.save()
            creative.account = self.account
            creative.ad_group = line_item
            creative.save()
            CreativeQueryManager.put(creative)

            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_line_item_detail',
                                    kwargs={'line_item_key': line_item.key()}),
            })

        else:
            errors = {}
            for key, value in creative_form.errors.items():
                # TODO: just join value?
                errors[key] = ' '.join([error for error in value])
            return JSONResponse({
                'errors': errors,
                'success': False,
            })


@login_required
def creative_form_new(request, *args, **kwargs):
    handler = CreativeFormHandler(id="line_item_key")
    return handler(request, use_cache=False, *args, **kwargs)


@login_required
def creative_form_edit(request, *args, **kwargs):
    handler = CreativeFormHandler(id="creative_key")
    return handler(request, use_cache=False, *args, **kwargs)


class DisplayCreativeHandler(RequestHandler):
    #asdf
    def get(self, creative_key):

        # Corner casing requests that are made for mraid.js.
        # This happens for MRAID creatives and can't be changed
        # because of the MRAID spec
        if creative_key == 'mraid.js':
            return HttpResponse("")

        creative = CreativeQueryManager.get(creative_key)
        if creative:
            if creative.ad_type == "image":
                template = """<html><head>
                <style type="text/css">body{margin:0;padding:0;}</style>
                </head><body><img src="%s"/></body></html>"""
                url_for_blob = helpers.get_url_for_blob(creative.image_blob)
                return HttpResponse(template % url_for_blob)

            if creative.ad_type == "text_icon":
                creative.icon_url = helpers.get_url_for_blob(creative.image_blob)
                return render_to_response(self.request,
                                          'advertiser/text_tile.html',
                                          {'c': creative})

            if creative.ad_type == "html":
                return HttpResponse("<html><body style='margin:0px;'>" + \
                                    creative.html_data + "</body></html")
        else:
            raise Http404


class CreativeImageHandler(RequestHandler):
    def get(self, creative_key):
        c = CreativeQueryManager.get(creative_key)
        if c and c.image:
            return HttpResponse(c.image, content_type='image/png')
        raise Http404


def creative_image(request, *args, **kwargs):
    return DisplayCreativeHandler()(request, *args, **kwargs)


def creative_html(request, *args, **kwargs):
    return DisplayCreativeHandler()(request, *args, **kwargs)

###########
# Helpers #
###########

def format_stats(all_stats):
    summed = reduce(lambda x, y: x + y, all_stats, StatsModel())
    stats = {
        'requests': {
            'today': all_stats[0].request_count,
            'yesterday': all_stats[1].request_count,
            'total': summed.request_count,
            'series': [int(s.request_count) for s in all_stats]
        },
        'impressions': {
            'today': all_stats[0].impression_count,
            'yesterday': all_stats[1].impression_count,
            'total': summed.impression_count,
            'series': [int(s.impression_count) for s in all_stats]
        },
        'users': {
            'today': all_stats[0].user_count,
            'yesterday': all_stats[1].user_count,
            'total': summed.user_count,
            'series': [int(s.user_count) for s in all_stats]
        },
        'ctr': {
            'today': ctr(all_stats[0].click_count,
                         all_stats[0].impression_count),
            'yesterday': ctr(all_stats[1].click_count,
                             all_stats[1].impression_count),
            'total': ctr(summed.click_count, summed.impression_count),
        },
        'clicks': {
            'today': all_stats[0].click_count,
            'yesterday': all_stats[1].click_count,
            'total': summed.click_count,
            'series': [int(s.click_count) for s in all_stats]
        },
    }
    return stats


def get_targeted_apps(adunits):
    # Database I/O could be made faster here by getting a list of
    # app keys and querying for the list, rather than querying
    # for each individual app. (au.app makes a query)
    targeted_apps = {}
    for adunit in adunits:
        app_key = str(adunit.app.key())
        app = targeted_apps.get(app_key)
        if not app:
            app = adunit.app
            app.adunits = []
            targeted_apps[app_key] = app
        targeted_apps[app_key].adunits += [adunit]
    return targeted_apps

