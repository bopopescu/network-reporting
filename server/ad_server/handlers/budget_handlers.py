from google.appengine.ext import webapp
from budget.views import budget_advance

class BudgetAdvanceHandler(webapp.RequestHandler):
    def get(self):
        response = budget_advance(None)
        self.response.out.write(response.content)