import tornado.ioloop
import tornado.web

from request_handlers import StatsHandler, StatsUpdateHandler

application = tornado.web.Application([
        (r"/stats", StatsHandler),
        (r"/update", StatsUpdateHandler),
], debug=False)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
