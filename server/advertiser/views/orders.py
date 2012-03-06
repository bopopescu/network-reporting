from common.utils.request_handler import RequestHandler
from common.ragendja.template import render_to_response

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
        return render_to_response(self.request,
                                  "advertiser/order_index.html",
                                  {})

def order_index(request, *args, **kwargs):
    return OrderIndexHandler()(request, use_cache=False, *args, **kwargs)


class OrderDetailHandler(RequestHandler):
    """
    @responsible: ignatius
    Top level stats rollup for all of the line items within the order.
    Lists each line item within the order with links to line item details.
    """
    def get(self):
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
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/order_form.html",
                                  {})

def order_form(request, *args, **kwargs):
    return OrderFormHandler()(request, use_cache=False, *args, **kwargs)


class LineItemFormHandler(RequestHandler):
    """
    @responsible: peter
    New/Edit form page for LineItems.
    """
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/lineitem_form.html",
                                  {})

def lineitem_form(request, *args, **kwargs):
    return LineItemFormHandler()(request, use_cache=False, *args, **kwargs)
