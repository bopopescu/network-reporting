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

from account.query_managers import AccountQueryManager
from advertiser.forms import OrderForm, LineItemForm
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager
from publisher.query_managers import AppQueryManager, AdUnitQueryManager

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
    def get(self, order_key):
        order = CampaignQueryManager.get(order_key)
        order_form = OrderForm(instance=order)
        return render_to_response(self.request,
                                  "advertiser/order_detail.html",
                                  {
                                    'order': order,
                                    'order_form': order_form})


@login_required
def order_detail(request, *args, **kwargs):
    return OrderDetailHandler()(request, use_cache=False, *args, **kwargs)


class LineItemDetailHandler(RequestHandler):
    """
    Almost identical to current campaigns detail page.
    """
    def get(self, order_key, line_item_key):
        order = CampaignQueryManager.get(order_key)
        line_item = AdGroupQueryManager.get(line_item_key)

        return render_to_response(self.request,
                                  "advertiser/line_item_detail.html",
                                  {
                                      'order': order,
                                      'line_item': line_item
                                  })


@login_required
def line_item_detail(request, *args, **kwargs):
    return LineItemDetailHandler()(request, use_cache=False, *args, **kwargs)


class OrderFormHandler(RequestHandler):
    """
    Edit order form handler which gets submitted from the order detail page.
    """
    def post(self, order_key):
        if not self.request.is_ajax():
            raise Http404

        # TODO: make sure order is part of account?
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

        return render_to_response(self.request,
                                  "advertiser/forms/order_and_line_item_form.html",
                                  {
                                      'apps': apps,
                                      'order': order,
                                      'order_form': order_form,
                                      'line_item': line_item,
                                      'line_item_form': line_item_form,
                                  })

    def post(self, order_key=None, line_item_key=None):
        if not self.request.is_ajax():
            raise Http404

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

            # TODO: go to order or line item detail page?
            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_order_detail', args=(order.key(),)),
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
def order_and_line_item_form(request, *args, **kwargs):
    return OrderAndLineItemFormHandler()(request, use_cache=False, *args, **kwargs)


###########
# Helpers #
###########

def format_stats_for_adgroup(adgroup):
    pass

def format_stats_for_campaign(campaign):
    pass

def format_stats(model):
    pass
