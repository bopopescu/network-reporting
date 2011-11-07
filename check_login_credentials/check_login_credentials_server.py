#!/usr/bin/python

import sys
sys.path.append('/home/ubuntu/mopub/check_login_credentials/')
sys.path.append('/home/ubuntu/mopub/server/')

import tornado.ioloop
import tornado.web

from request_handlers.check_login_credentials_handler import CheckLoginCredentialsHandler

application = tornado.web.Application([
        (r'/(.*)', CheckLoginCredentialsHandler),
], debug=False)

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        application.listen(sys.argv[1])
    else:
        application.listen(80)
    tornado.ioloop.IOLoop.instance().start()
