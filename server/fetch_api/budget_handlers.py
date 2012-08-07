from google.appengine.ext import webapp

from budget.query_managers import BudgetQueryManager


class BudgetUpdateOrCreateHandler(webapp.RequestHandler):

    def post(self):
        adgroup_keys = self.request.get_all('adgroup_keys')
        BudgetQueryManager.update_or_create_budgets_for_adgroup_keys(
            adgroup_keys)
