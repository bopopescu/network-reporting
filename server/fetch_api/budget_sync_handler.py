from urllib import urlencode
import logging

from google.appengine.ext import webapp, db
from google.appengine.api import urlfetch, taskqueue


from advertiser.models import Campaign
from budget.models import (BudgetSliceLog, 
                           BudgetSliceCounter,
                           BudgetSliceSyncStatus,
                           )
from adserver_constants import (ADSERVER_HOSTNAME,
                                BUDGET_SYNC_URL,
                                )

SYNC_SUCC = 'gae_to_ec2_sync_success'
SYNC_FAIL = 'gae_to_ec2_sync_fail'

class BudgetSyncHandler(webapp.RequestHandler):

    def get(self):
        slice_num = int(self.request.get('slice_num'))
        total_spent = float(self.request.get('total_spent'))
        campaign_key = self.request.get('campaign_key')
        campaign = Campaign.get(campaign_key)
        budget = campaign.budget_obj
        slice_log = budget.timeslice_logs.filter('slice_num =', slice_num).get()
        if not slice_log.ec2_synced:
            budget.total_spent += total_spent
            slice_log.actual_spending += total_spent
            slice_log.ec2_spending = total_spent
            slice_log.ec2_synced = True
            try:
                # Make a single transaction?
                db.put([budget, slice_log])
            except Exception, e:
                raise Exception("Error putting budget")
        self.response.out.write('SYNCED')

class BudgetSyncCronHandler(webapp.RequestHandler):

    def get(self):
        # There is only one!
        master_counter = BudgetSliceCounter.all().get()
        statuses = BudgetSliceSyncStatus.all().filter('slice_num >', \
            master_counter.last_synced_slice).fetch(master_counter.unsynced_slices)
        status_dict = {}
        # Build dict of statuses so we cna sort and updated the last_synced_slice
        for status in statuses:
            status_dict[status.slice_num] = status.synced

        last_synced_slice = master_counter.last_synced_slice
        for key in sorted(status_dict.keys()):
            if not status_dict[key]:
                break
            last_synced_slice = status_dict[key]

        master_counter.last_synced_slice = last_synced_slice
        master_counter.put()
        # range over all unsynced completed slices
        for slice_num in range(last_synced_slice+1, master_counter.slice_num):
            taskqueue.add(url='/fetch_api/budget/sync/worker',
                          method='GET',
                          queue_name='budget-api',
                          params={'slice_num': slice_num})



class BudgetSyncWorker(webapp.RequestHandler):

    def get(self):
        slice_num = int(self.request.get('slice_num'))
        status = BudgetSliceSyncStatus.all().filter('slice_num =', slice_num).get()
        if status is None:
            status = BudgetSliceSyncStatus(slice_num=slice_num,
                                           synced=False,
                                           )
            status.put()
        # If a previous slice has not synced completely but this one has,
        # ignore this set of slices
        if status.synced:
            return
        logs = BudgetSliceLog.all().filter('slice_num =', slice_num).fetch(10000)
        waiting_nums = [log.slice_num for log in logs]
        updated_logs = []
        statuses = {}
        rpcs = []
        no_spending = []
        for log in logs:
            if log.gae_synced:
                waiting_nums.remove(log.slice_num)
                continue
            if log.sync_spending == 0.0:
                waiting_nums.remove(log.slice_num)
                log.gae_synced = True
                no_spending.append(log)
                continue
            rpcs.append(build_sync_to_ec2_rpc(log, waiting_nums, statuses, updated_logs))
        if no_spending:
            db.put(no_spending)
        for rpc in rpcs:
            if rpc is not None:
                rpc.wait()

def build_sync_to_ec2_rpc(slice_log, wait_list, status_dict, updated_logs):
    rpc = urlfetch.create_rpc()
    callback = build_sync_to_ec2_callback(rpc, slice_log, wait_list, status_dict, updated_logs)
    rpc.callback = callback
    camp = slice_log.budget.campaign.get()
    if camp is None:
        wait_list.remove(slice_log.slice_num)
        return
    query_dict = dict(campaign_key = str(slice_log.budget.campaign.get().key()),
                      slice_num=slice_log.slice_num,
                      total_spent=slice_log.sync_spending)
    qs = urlencode(query_dict)
    full_url = 'http://' + ADSERVER_HOSTNAME + BUDGET_SYNC_URL + '?' + qs
    logging.info(full_url)
    urlfetch.make_fetch_call(rpc, full_url, method=urlfetch.GET)
    return rpc


def build_sync_to_ec2_callback(rpc, slice_log, wait_list, status_dict, updated_logs):
    def handle_result():
        result = rpc.get_result()
        if result.status_code >= 500:
            handle_sync_to_ec2_error(slice_log, wait_list, status_dict, updated_logs)
            return
        data = result.content
        logging.info(data)
        if data not in ['SYNCED', u'SYNCED']:
            handle_sync_to_ec2_error(slice_log, wait_list, status_dict, updated_logs)
            return
        # Successful sync! mark the appropriate fields
        status_dict[slice_log.slice_num] = SYNC_SUCC
        slice_log.gae_synced = True
        updated_logs.append(slice_log)
        wait_list.remove(slice_log.slice_num)
        # If this is the last callback we're waiting on finalize this sync
        if wait_list == []:
            finalize_sync(status_dict, updated_logs)
    return handle_result

def handle_sync_to_ec2_error(slice_log, wait_list, status_dict, updated_logs):
    logging.warning("error syncing %s" % slice_log)
    status_dict[slice_log.slice_num] = SYNC_FAIL
    wait_list.remove(slice_log.slice_num)
    if wait_list == []:
        finalize_sync(status_dict, updated_logs)

def finalize_sync(status_dict, updated_logs):
    # Batch put all the updated logs
    db.put(updated_logs)
    fully_synced = True
    for status in status_dict.values():
        if status == SYNC_FAIL:
            fully_synced = False
            break
    if fully_synced:
        status = BudgetSliceSyncStatus.all().filter('slice_num =', slice_num).get()
        status.synced = True
        status.put()














