import json
from utils.decorators import web_dec
import tornado.web

class StatsUpdateHandler(tornado.web.RequestHandler):
    @web_dec
    def get(self):
        self.write("stats update handler ok!!")
