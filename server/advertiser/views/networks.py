import datetime

from common.utils.request_handler import RequestHandler
from common.ragendja.template import render_to_response
from django.contrib.auth.decorators import login_required
from common.utils.timezones import Pacific_tzinfo

from advertiser.query_managers import CampaignQueryManager


class NetworkIndexHandler(RequestHandler):
    def get(self):
        today = datetime.datetime.now(Pacific_tzinfo()).date()
        yesterday = today - datetime.timedelta(days=1)

        if not self.start_date:
            self.start_date = today - datetime.timedelta(days=self.date_range)
        end_date = self.start_date + datetime.timedelta(days=self.date_range)

        today_index = (today - self.start_date).days if today >= self.start_date and today <= end_date else None
        yesterday_index = (yesterday - self.start_date).days if yesterday >= self.start_date and yesterday <= end_date else None

        network_adgroups = []
        for campaign in CampaignQueryManager.get_network_campaigns(account=self.account):
            for adgroup in campaign.adgroups:
                network_adgroups.append(adgroup)
        # sort alphabetically
        network_adgroups.sort(key=lambda adgroup: adgroup.campaign.name.lower())

        return render_to_response(self.request,
                                  "advertiser/network_index.html",
                                  {
                                      'network_adgroups': network_adgroups,
                                      'start_date': self.start_date,
                                      'end_date': end_date,
                                      'date_range': self.date_range,
                                      'today': today_index,
                                      'yesterday': yesterday_index,
                                      'offline': self.offline,
                                  })


@login_required
def network_index(request, *args, **kwargs):
    return NetworkIndexHandler()(request, *args, **kwargs)
