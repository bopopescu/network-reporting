from google.appengine.ext import webapp
from google.appengine.api import urlfetch, taskqueue

from budget.query_managers import BudgetQueryManager


class BudgetUpdateOrCreateHandler(webapp.RequestHandler):

    def post(self):
        campaign_keys = self.request.get_all('campaign_keys')
        BudgetQueryManager.update_or_create_budgets_for_campaign_keys(campaign_keys)