import datetime
import logging

from common.utils.request_handler import RequestHandler
from common.ragendja.template import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from common.utils.timezones import Pacific_tzinfo

from advertiser.query_managers import AdvertiserQueryManager
from advertiser.models import AdGroup, NetworkStates


class NetworkIndexHandler(RequestHandler):
    """
    Deprecated
    """
    def get(self):
        today = datetime.datetime.now(Pacific_tzinfo()).date()
        yesterday = today - datetime.timedelta(days=1)

        today_index = (today - self.start_date).days if today >= \
                self.start_date and today <= self.end_date else None
        yesterday_index = (yesterday - self.start_date).days if yesterday >= \
                self.start_date and yesterday <= self.end_date else None

        # Get all adgroups.
        all_adgroups = AdvertiserQueryManager.get_adgroups_dict_for_account(
                self.account).values()

        # We need to loop through all of the adgroups to determine which are network campaigns.
        # Normally, this would trigger a lot of sequential GETs (to obtain the campaign for each
        # adgroup). However, we get around this by doing a batch (potentially memcached) GET of all
        # campaigns and then manually populating the "campaign" property for each adgroup.
        campaigns_dict = AdvertiserQueryManager.get_campaigns_dict_for_account(self.account,
                                                                               include_deleted=True)
        adgroups = []
        for adgroup in all_adgroups:
            campaign_key = str(AdGroup.campaign.get_value_for_datastore(
                adgroup))
            if campaign_key in campaigns_dict:
                adgroup.campaign = campaigns_dict[campaign_key]
                adgroups.append(adgroup)

        # Filter down to only network campaigns and sort alphabetically.
        network_adgroups = filter(lambda a: a.campaign.campaign_type ==
                'network' and a.campaign.network_state ==
                NetworkStates.STANDARD_CAMPAIGN, adgroups)
        network_adgroups.sort(key=lambda a: a.campaign.name.lower())

        return render_to_response(self.request,
                                  "advertiser/network_index.html",
                                  {
                                      'account': self.account,
                                      'network_adgroups': network_adgroups,
                                      'start_date': self.start_date,
                                      'end_date': self.end_date,
                                      'date_range': self.date_range,
                                      'today': today_index,
                                      'yesterday': yesterday_index,
                                      'offline': self.offline,
                                  })


@login_required
def network_index(request, *args, **kwargs):
    return NetworkIndexHandler()(request, use_cache=False, *args, **kwargs)

