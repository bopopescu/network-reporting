import logging
from datetime import datetime, date

from common.utils.request_handler import RequestHandler
from common.utils import simplejson as json
from common.ragendja.template import JSONResponse

from api.networks_helpers import get_all_stats

class NetworksApi(RequestHandler):
    def get(self):
        app_key = self.request.GET.get('app')
        network = self.request.GET.get('network')
        account_key = self.request.GET.get('account')

        start_date = datetime.strptime(self.request.GET.get('start_date'),
                '%Y-%m-%d').date()
        end_date = datetime.strptime(self.request.GET.get('end_date'),
                '%Y-%m-%d').date()

        all_stats = get_all_stats(app_key, network, account_key,
                start_date, end_date)

        return JSONResponse({'status': 200,
                             'all_stats': all_stats})

    def post(self):
        post_dict = json.loads(self.request.raw_post_data)
        arg_list = post_dict['arg_list']

        start_date = datetime.strptime(post_dict['start_date'],
                '%Y-%m-%d').date()
        end_date = datetime.strptime(post_dict['end_date'],
                '%Y-%m-%d').date()

        # get stats for each arg in the arg list and put them into a single
        # dict
        temp_stats = [get_all_stats(args['app'], args['network'],
            args['account'], start_date, end_date).items() for args in
            arg_list]
        all_stats = dict(sum(temp_stats, []))

        return JSONResponse({'status': 200,
                             'all_stats': all_stats})

def networks_api(request, *args, **kwargs):
    return NetworksApi()(request, *args, **kwargs)

