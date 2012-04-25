from google.appengine.ext import webapp
from budget.views import budget_advance, advance_worker

class BudgetAdvanceHandler(webapp.RequestHandler):
    def get(self):
        response = budget_advance(None)
        self.response.out.write(response.content)

class BudgetAdvanceWorkerHandler(webapp.RequestHandler):
    def post(self):
        resp = advance_worker(self.request, 
                              key_shard=self.request.get('key_shard'))
        self.response.out.write(resp.content)
