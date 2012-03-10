__doc__ = """
Views for orders and line items.

'Order' is an alias for 'Campaign', and 'LineItem' is an alias for
'AdGroup'.  We decided to make this change because many other
advertisers use this language.  The code hasn't adopted this naming
convention, and instead still uses "Campaign" and "AdGroup" for
compatibility with the ad server.

Whenever you see "Campaign", think "Order", and wherever you see
"""

from django.core.urlresolvers import reverse

from common.utils.request_handler import RequestHandler
from common.ragendja.template import JSONResponse, render_to_response

from advertiser.forms import OrderForm, LineItemForm
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager
from reporting.query_managers import StatsModelQueryManager

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
        stats_manager = StatsModelQueryManager(self.account, offline=self.offline)
        orders = CampaignQueryManager.get_campaigns(account=self.account)
        for order in orders:
            order.lineitems = AdGroupQueryManager.get_adgroups(campaign=order)
            for lineitem in order.lineitems:
                s = stats_manager.get_stats_for_days(advertiser=lineitem,
                                                     days = self.days)
                # we keep stats as lists so we can do sparklines
                # there will be an int for each day in self.days
                lineitem.requests = [int(d.request_count) for d in s]
                lineitem.impressions = [int(d.impression_count) for d in s]
                lineitem.clicks = [int(d.click_count) for d in s]
                lineitem.conversions = [int(d.conversion_count) for d in s]


        # Summarize the stats for the rollup
        # Each of the line item-level stats are kept as lists (so we can do sparklines).
        # We have to sum them first, and then sum all of the lineitem stats in the adgroup.
        # That's why theres two sums, like sum([sum(i) for i in j])
        # REFACTOR: do this over ajax
        total_impressions = sum([sum(li.impressions) for li in order.lineitems for order in orders])
        total_clicks = sum([sum(li.clicks) for li in order.lineitems for order in orders])
        total_conversions = sum([sum(li.conversions) for li in order.lineitems for order in orders])
        totals = {
            "impressions": total_impressions,
            "clicks" : total_clicks,
            "ctr": ctr(total_clicks, total_impressions),
            "conversions": total_conversions
        }

        return render_to_response(self.request,
                                  "advertiser/order_index.html",
                                  {
                                      'orders': orders,
                                      'totals': totals
                                  })

def order_index(request, *args, **kwargs):
    return OrderIndexHandler()(request, use_cache=False, *args, **kwargs)


class OrderDetailHandler(RequestHandler):
    """
    @responsible: ignatius
    Top level stats rollup for all of the line items within the order.
    Lists each line item within the order with links to line item details.
    """
    def get(self, campaign_key):

        return render_to_response(self.request,
                                  "advertiser/order_detail.html",
                                  {})

def order_detail(request, *args, **kwargs):
    return OrderDetailHandler()(request, use_cache=False, *args, **kwargs)


class LineItemDetailHandler(RequestHandler):
    """
    @responsible: ignatius
    Almost identical to current campaigns detail page.
    """
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/lineitem_detail.html",
                                  {})

def lineitem_detail(request, *args, **kwargs):
    return LineItemDetailHandler()(request, use_cache=False, *args, **kwargs)


class LineItemArchiveHandler(RequestHandler):
    """
    @responsible: pena
    """
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/lineitem_archive.html",
                                  {})

def lineitem_archive(request, *args, **kwargs):
    return LineItemArchiveHandler()(request, use_cache=False, *args, **kwargs)


class OrderFormHandler(RequestHandler):
    """
    @responsible: peter
    New/Edit form page for Orders. With each new order, a new line
    item is required
    """
    def get(self, order_key=None):
        if order_key:
            instance = CampaignQueryManager.get(key=order_key)
        else:
            instance = None

        order_form = OrderForm(instance=instance)

        return render_to_response(self.request, "advertiser/order_form.html",
                                  {
                                      'order_form': order_form,
                                  })

    def post(self, order_key=None):
        if order_key:
            instance = CampaignQueryManager.get(key=order_key)
        else:
            instance = None

        order_form = OrderForm(self.request.POST, instance=instance)

        if order_form.is_valid():
            order = order_form.save()
            order.account = self.account
            order.save()

            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_order_details', args=(order.key(),)),
            })

        else:
            errors = {}
            for key, value in order_form.errors.items():
                errors[key] = ' '.join([error for error in value])

            return JSONResponse({
                'errors': errors,
                'success': False,
            })

        return render_to_response(self.request, "advertiser/order_form.html",
                                  {
                                      'order_form': order_form,
                                  })


def order_form(request, *args, **kwargs):
    return OrderFormHandler()(request, use_cache=False, *args, **kwargs)


class LineItemFormHandler(RequestHandler):
    """
    @responsible: peter
    New/Edit form page for LineItems.
    """
    def get(self, order_key, line_item_key=None):
        line_item_form = LineItemForm()
        return render_to_response(self.request,
                                  "advertiser/line_item_form.html",
                                  {
                                      'line_item_form': line_item_form,
                                  })


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
