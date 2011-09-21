import json
from utils.decorators import web_dec
import tornado.web

class StatsHandler(tornado.web.RequestHandler):
    @web_dec
    def get(self):
        self.write("stats handler ok!!")
