import tornado.ioloop
import tornado.web

from request_handlers.check_login_credentials import CheckLoginCredentialsHandler

application = tornado.web.Application([
        (r'^$', TestLoginCredentialsHandler),
], debug=False)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
