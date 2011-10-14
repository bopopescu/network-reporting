#!/usr/bin/python

import sys
sys.path.append('/home/ubuntu/mopub_experimental/check_login_credentials/request_handlers')

import tornado.ioloop
import tornado.web

from check_login_credentials_handler import CheckLoginCredentialsHandler

application = tornado.web.Application([
        (r'/(.*)', CheckLoginCredentialsHandler),
], debug=False)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
