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

import logging

ctr = lambda clicks, impressions: (clicks/float(impressions) if impressions
        else 0)

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

        # Grab all of the orders, and for each order, grab all of the line items.
        # For each of the line items, grab the stats for the date range.
        # REFACTOR: do this over ajax
        orders = CampaignQueryManager.get_campaigns(account=self.account)

        return render_to_response(self.request,
                                  "advertiser/order_index.html",
                                  {
                                      'orders': orders,

                                      'start_date': self.start_date,
                                      'end_date': self.end_date,
                                      'date_range': self.date_range,
                                  })


@login_required
def order_index(request, *args, **kwargs):
    return OrderIndexHandler()(request, use_cache=False, *args, **kwargs)


class OrderDetailHandler(RequestHandler):
    """
    Top level stats rollup for all of the line items within the order.
    Lists each line item within the order with links to line item details.
    """
    def get(self, campaign_key):

        return render_to_response(self.request,
                                  "advertiser/order_detail.html",
                                  {})


@login_required
def order_detail(request, *args, **kwargs):
    return OrderDetailHandler()(request, use_cache=False, *args, **kwargs)


class LineItemDetailHandler(RequestHandler):
    """
    Almost identical to current campaigns detail page.
    """
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/lineitem_detail.html",
                                  {})


@login_required
def lineitem_detail(request, *args, **kwargs):
    return LineItemDetailHandler()(request, use_cache=False, *args, **kwargs)


class OrderFormHandler(RequestHandler):
    """
    New/Edit form page for Orders. With each new order, a new line
    item is required
    """
    def get(self, order_key=None):
        if order_key:
            instance = CampaignQueryManager.get(order_key)
        else:
            instance = None

        order_form = OrderForm(instance=instance)

        return render_to_response(self.request,
                                  "advertiser/order_form.html",
                                  {
                                      'order_form': order_form,
                                  })

    def post(self, order_key=None):
        if order_key:
            instance = CampaignQueryManager.get(order_key)
        else:
            instance = None

        order_form = OrderForm(self.request.POST, instance=instance)

        if order_form.is_valid():
            order = order_form.save()
            order.account = self.account
            order.save()

            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_order_detail', args=(order.key(),)),
            })

        else:
            errors = {}
            for key, value in order_form.errors.items():
                errors[key] = ' '.join([error for error in value])

            return JSONResponse({
                'errors': errors,
                'success': False,
            })


@login_required
def order_form(request, *args, **kwargs):
    return OrderFormHandler()(request, use_cache=False, *args, **kwargs)


class LineItemFormHandler(RequestHandler):
    """
    New/Edit form page for LineItems.
    """
    def get(self, order_key, line_item_key=None):
        if order_key:
            order = CampaignQueryManager.get(order_key)
        else:
            order = None

        if line_item_key:
            instance = AdGroupQueryManager.get(line_item_key)
        else:
            instance = None

        line_item_form = LineItemForm(instance=instance)

        return render_to_response(self.request,
                                  "advertiser/line_item_form.html",
                                  {
                                      'line_item_form': line_item_form,
                                      'order': order,
                                  })

    def post(self, order_key, line_item_key=None):
        if order_key:
            order = CampaignQueryManager.get(order_key)
        else:
            order = None

        if line_item_key:
            instance = AdGroupQueryManager.get(line_item_key)
        else:
            instance = None

        line_item_form = LineItemForm(self.request.POST, instance=instance)

        if line_item_form.is_valid():
            line_item = line_item_form.save()
            line_item.account = self.account
            line_item.order = order
            line_item.save()

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
def line_item_form(request, *args, **kwargs):
    return LineItemFormHandler()(request, use_cache=False, *args, **kwargs)


###########
# Helpers #
###########

def format_stats_for_adgroup(adgroup):
    pass

def format_stats_for_campaign(campaign):
    pass

def format_stats(model):
    pass
