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
from django.http import Http404
from django.utils import simplejson

from common.utils.request_handler import RequestHandler
from common.ragendja.template import JSONResponse, render_to_response

from account.query_managers import AccountQueryManager
from advertiser.forms import (OrderForm, LineItemForm, BaseCreativeForm,
                              ImageCreativeForm, TextAndTileCreativeForm,
                              HtmlCreativeForm)
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager
from publisher.query_managers import AppQueryManager, AdUnitQueryManager
from reporting.query_managers import StatsModelQueryManager
from reporting.models import StatsModel

import logging


flatten = lambda l: [item for sublist in l for item in sublist]

ctr = lambda clicks, impressions: \
      (clicks/float(impressions) if impressions else 0)


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
        logging.warn(orders)
        return {
            'orders': orders,
        }

@login_required
def order_index(request, *args, **kwargs):
    t = "advertiser/order_index.html"
    return OrderIndexHandler(template=t)(request, use_cache=False, *args, **kwargs)
        

class LineItemIndexHandler(RequestHandler):
    """
    Very similar to the order index handler, displays a list of active
    (non-deleted) orders.
    """
    def get(self, *args, **kwargs):
        line_items = AdGroupQueryManager.get_adgroups(account=self.account)
        line_items = [l for l in line_items if not (l.campaign.advertiser == "marketplace")]
        return {
            'line_items': line_items
        }


@login_required
def line_item_index(request, *args, **kwargs):
    t = "advertiser/line_item_index.html"
    return LineItemIndexHandler(template=t)(request, *args, **kwargs)

    
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
        all_stats = stats_q.get_stats_for_days(advertiser=order,
                                                     days = self.days)

        # Get the targeted adunits and group them by their app.
        targeted_adunits = flatten([AdUnitQueryManager.get(line_item.site_keys) \
                                    for line_item in order.adgroups])
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

<<<<<<< HEAD
        # Get the metadata for the lineitem and its order
=======
        # Get the metadata for the lineitem
>>>>>>> dda6c84b9eb87ba875d444c8c0f2485d48bf4504
        line_item = AdGroupQueryManager.get(line_item_key)
        order = line_item.campaign

        # Create creative forms
        base_creative_form = BaseCreativeForm()
        image_creative_form = ImageCreativeForm()
        text_tile_creative_form = TextAndTileCreativeForm()
        html_creative_form = HtmlCreativeForm()

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
            'base_creative_form': base_creative_form,
            'text_tile_creative_form': text_tile_creative_form,
            'image_creative_form': image_creative_form,
            'html_creative_form': html_creative_form,
            'stats': format_stats(all_stats),
            'targeted_apps': targeted_apps.values(),
            'targeted_app_keys': targeted_apps.keys()
        }


@login_required
def line_item_detail(request, *args, **kwargs):
    t = "advertiser/lineitem_detail.html"
    return LineItemDetailHandler(template=t, id="line_item_key")(request, use_cache=False, *args, **kwargs)


class AdSourceStatusChangeHandler(RequestHandler):
    """
    Changes the status of a line item or list of line items.
    """
    def post(self):
        # Pull out the params
        ad_sources = self.request.POST.getlist('ad_sources[]')
        status = self.request.POST.get('status', None)

        if ad_sources and status:
            for ad_source_key in ad_sources:
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
                        ad_source.archived = False
                        updated = True
                    elif status == 'pause':
                        ad_source.active = False
                        ad_source.archived = False
                        updated = True
                    elif status == 'archive':
                        ad_source.active = False
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
    def get(self, order_key):
        raise Http404

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
            order_form = OrderForm(self.request.POST, instance=order, prefix='order')

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

            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_line_item_detail',
                                    args=(order.key(), line_item.key())),
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
    template = "advertiser/forms/order_and_line_item_form.html",
    return OrderAndLineItemFormHandler(template=template)(request, use_cache=False, *args, **kwargs)


class CreativeFormHandler(RequestHandler):
    def get(self, order_key, line_item_key, creative_key=None):
        raise Http404

    def post(self, order_key, line_item_key, creative_key=None):
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

        if creative_form.is_valid():

            return JSONResponse({
                'success': True,
                'redirect': reverse('advertiser_line_item_detail',
                                    args=(order.key(), line_item.key())),
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
def creative_form(request, *args, **kwargs):
    template = "advertiser/forms/order_and_line_item_form.html",
    return OrderAndLineItemFormHandler(template=template)(request, use_cache=False, *args, **kwargs)


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
