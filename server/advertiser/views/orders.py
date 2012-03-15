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

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from common.utils.request_handler import RequestHandler
from common.ragendja.template import JSONResponse, render_to_response

from advertiser.forms import OrderForm, LineItemForm
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager
from publisher.query_managers import AppQueryManager

import logging

ctr = lambda clicks, impressions: \
      (clicks/float(impressions) if impressions else 0)

class OrderIndexHandler(RequestHandler):
    """
    @responsible: pena
    Shows a list of orders and line items.
    Orders show:
      - name, status, advertiser, and a top-level stats rollup.
    Line Items show:
      - name, dates, budgeting information, top-level stats.
    """
    def get(self):


        orders = CampaignQueryManager.get_order_campaigns(account=self.account)

        # Stats for stats breakdown and graph.

        return {
            'orders': orders,
            'stats': format_stats_for_campaign(0)
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
        order = CampaignQueryManager.get(order_key)
        order_form = OrderForm(instance=order)
        return {
            'order': order,
            'order_form': order_form,
            'stats': format_stats_for_campaign(order)
        }


@login_required
def order_detail(request, *args, **kwargs):
    t = "advertiser/order_detail.html"
    return OrderDetailHandler(template=t, id="order_key")(request, use_cache=False, *args, **kwargs)


class LineItemDetailHandler(RequestHandler):
    """
    Almost identical to current campaigns detail page.
    """
    def get(self, order_key, line_item_key):
        
        order = CampaignQueryManager.get(order_key)
        line_item = AdGroupQueryManager.get(line_item_key)

        return {
            'order': order,
            'line_item': line_item,
            'stats': format_stats_for_adgroup(line_item)
        }


@login_required
def line_item_detail(request, *args, **kwargs):
    t = "advertiser/lineitem_detail.html"
    return LineItemDetailHandler(template=t)(request, use_cache=False, *args, **kwargs)


class OrderFormHandler(RequestHandler):
    """
    Edit order form handler which gets submitted from the order detail page.
    """
    def post(self, order_key):
        instance = CampaignQueryManager.get(order_key)
        order_form = OrderForm(self.request.POST, instance=instance)

        if order_form.is_valid():
            order = order_form.save()
            order.save()
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
    return OrderFormHandler()(request, use_cache=False, *args, **kwargs)


class OrderAndLineItemFormHandler(RequestHandler):
    """
    New/Edit form page for Orders and LineItems.
    """
    def get(self, order_key=None, line_item_key=None):
        if order_key:
            # TODO: make sure order belongs to account
            order = CampaignQueryManager.get(order_key)
            if line_item_key:
                # TODO: make sure line item belongs to account
                # TODO: make sure line item belongs to order
                line_item = AdGroupQueryManager.get(line_item_key)
            else:
                line_item = None
        else:
            order = None
            # TODO: make sure line_item_key is None
            line_item = None

        order_form = OrderForm(instance=order)
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
        if order_key:
            # TODO: make sure order belongs to account
            order = CampaignQueryManager.get(order_key)
            if line_item_key:
                # TODO: make sure line item belongs to account
                # TODO: make sure line item belongs to order
                line_item = AdGroupQueryManager.get(line_item_key)
            else:
                line_item = None
        else:
            order = None
            # TODO: make sure line_item_key is None
            line_item = None

        if not order:
            order_form = OrderForm(self.request.POST, instance=order)

            if order_form.is_valid():
                order = order_form.save()
                order.account = self.account
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

        line_item_form = LineItemForm(self.request.POST, instance=line_item)

        if line_item_form.is_valid():
            line_item = line_item_form.save()
            line_item.account = self.account
            line_item.campaign = order
            line_item.save()
            AdGroupQueryManager.put(line_item)

            # TODO: go to order or line item detail page?
            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_order_detail', args=(order.key(),)),
            })

        else:
            errors = {}
            for key, value in line_item_form.errors.items():
                errors[key] = ' '.join([error for error in value])

            return JSONResponse({
                'errors': errors,
                'success': False,
            })


@login_required
def order_and_line_item_form(request, *args, **kwargs):
    t = "advertiser/forms/order_and_line_item_form.html",
    return OrderAndLineItemFormHandler(template=t)(request, use_cache=False, *args, **kwargs)


###########
# Helpers #
###########

def format_stats_for_adgroup(adgroup):
    stats = {
        'requests': {
            'today': 0,
            'yesterday': 0,
            'total': 0,
        },
        'impressions': {
            'today': 0,
            'yesterday': 0,
            'total': 0,
        },
        'users': {
            'today': 0,
            'yesterday': 0,
            'total': 0
        },
        'ctr': {
            'today': 0,
            'yesterday': 0,
            'total': 0
        },
        'clicks': {
            'today': 0,
            'yesterday': 0,
            'total': 0
        },
    }
    return stats


def format_stats_for_campaign(campaign):
    stats = {
        'requests': {
            'today': 0,
            'yesterday': 0,
            'total': 0,
        },
        'impressions': {
            'today': 0,
            'yesterday': 0,
            'total': 0,
        },
        'users': {
            'today': 0,
            'yesterday': 0,
            'total': 0
        },
        'ctr': {
            'today': 0,
            'yesterday': 0,
            'total': 0
        },
        'clicks': {
            'today': 0,
            'yesterday': 0,
            'total': 0
        },
    }
    return stats

def format_stats(model):
    pass
