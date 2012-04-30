#!/usr/bin/env python
from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from fetch_api.auc_fetch_handler import (AUCFetchHandler, 
                                         AUCUserPushHandler,
                                         AUCUserPushFanOutHandler,
                                         )
from fetch_api.budget_sync_handler import (BudgetSyncHandler,
                                           BudgetSyncCronHandler,
                                           BudgetSyncWorker,
                                           )
from fetch_api.budget_handlers import BudgetUpdateOrCreateHandler


def main():
    app = webapp.WSGIApplication([
            ('/fetch_api/adunit/(?P<adunit_key>[-\w\.]+)/fetch_context', AUCFetchHandler),
            (r'/fetch_api/adunit_update_push', AUCUserPushHandler),
            (r'/fetch_api/adunit_update_fanout', AUCUserPushFanOutHandler),
            (r'/fetch_api/budget/sync', BudgetSyncHandler),
            (r'/fetch_api/budget/sync/cron', BudgetSyncCronHandler),
            (r'/fetch_api/budget/sync/worker', BudgetSyncWorker),
            (r'/fetch_api/budget/update_or_create', BudgetUpdateOrCreateHandler),
            ])
    run_wsgi_app(app)

if __name__ == '__main__':
    main()
