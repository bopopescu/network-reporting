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

from common.utils.request_handler import RequestHandler
from common.ragendja.template import render_to_response

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
        orders = CampaignQueryManager.get_campaigns(account=self.account)

        return render_to_response(self.request,
                                  "advertiser/order_index.html",
                                  {
                                      'orders': orders,

                                      'start_date': self.start_date,
                                      'end_date': self.end_date,
                                      'date_range': self.date_range,
                                  })

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

def lineitem_detail(request, *args, **kwargs):
    return LineItemDetailHandler()(request, use_cache=False, *args, **kwargs)


class LineItemArchiveHandler(RequestHandler):
    """
    """

    def get(self):

        archived_lineitems = AdGroupQueryManager.get_adgroups(account=self.account,
                                                             archived=True)
        return render_to_response(self.request,
                                  "advertiser/lineitem_archive.html",
                                  {
                                      'archived_lineitems': archived_lineitems
                                  })

def lineitem_archive(request, *args, **kwargs):
    return LineItemArchiveHandler()(request, use_cache=False, *args, **kwargs)


class OrderFormHandler(RequestHandler):
    """
    New/Edit form page for Orders. With each new order, a new line
    item is required
    """
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/order_form.html",
                                  {})

def order_form(request, *args, **kwargs):
    return OrderFormHandler()(request, use_cache=False, *args, **kwargs)


class LineItemFormHandler(RequestHandler):
    """
    New/Edit form page for LineItems.
    """
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/lineitem_form.html",
                                  {})

def lineitem_form(request, *args, **kwargs):
    return LineItemFormHandler()(request, use_cache=False, *args, **kwargs)

