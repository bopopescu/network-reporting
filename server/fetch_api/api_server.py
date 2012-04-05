#!/usr/bin/env python
from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from fetch_api.auc_fetch_handler import AUCFetchHandler, AUCUserPushHandler
from fetch_api.budget_sync_handler import (BudgetSyncHandler,
                                           BudgetSyncCronHandler,
                                           BudgetSyncWorker,
                                           )


def main():
    app = webapp.WSGIApplication([
            ('/fetch_api/adunit/(?P<adunit_key>[-\w\.]+)/fetch_context', AUCFetchHandler),
            ('/fetch_api/adunit_update_push', AUCUserPushHandler),
            (r'/fetch_api/budget/sync', BudgetSyncHandler),
            (r'/fetch_api/budget/sync/cron', BudgetSyncCronHandler),
            (r'/fetch_api/budget/sync/worker', BudgetSyncWorker),
            ])
    run_wsgi_app(app)

if __name__ == '__main__':
    main()