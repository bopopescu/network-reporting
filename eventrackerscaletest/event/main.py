import random
import time
import os
import logging
import uuid

import urllib
import urllib2

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.api import namespace_manager
from google.appengine.api.taskqueue import Task


from event.models import DimensionOneLevelOne, DimensionTwoLevelOne
from async.main import log

from userstore.models import MobileUser


def event_log(log_type,logging_params):

    if log_type == "0":
        logging.info("logging with internal service")
        deadline = self.request.get("deadline")
        deadline = float(deadline) if deadline else None    
        rpc = urlfetch.create_rpc(deadline=deadline) 
        data = urllib.urlencode(logging_params)
        url = "http://eventrackerscaletest.appspot.com/log/one"
        # url = "http://1-logging.latest.eventrackerscaletest.appspot.com/log/one"
        # url = "http://localhost:8081/log/one"
        # logging.info("URL: %s with deadline: %s"%(url+"?"+data,deadline))
        urlfetch.make_fetch_call(rpc,url+"?"+data,
                                headers={'X-URLFetch-Service-Id': 'APPSPOT'},
                                follow_redirects=False)
        try:
            result = rpc.get_result()
            if result.status_code == 200:
                html = result.content
            else:
                html = "ERROR"    
        except urlfetch.DownloadError:
            html = None
        html = "WHO CARES"
    elif log_type == "1":
        logging.info("logging with external service")
        deadline = self.request.get("deadline")
        deadline = float(deadline) if deadline else None    
        rpc = urlfetch.create_rpc(deadline=deadline) 
        data = urllib.urlencode(logging_params)
        url = "http://eventrackerscaletest.appspot.com/log/one"
        # url = "http://1-logging.latest.eventrackerscaletest.appspot.com/log/one"
        # url = "http://localhost:8081/log/one"
        # logging.info("URL: %s with deadline: %s"%(url+"?"+data,deadline))
        urlfetch.make_fetch_call(rpc,url+"?"+data)
        try:
            result = rpc.get_result()
            if result.status_code == 200:
                html = result.content
            else:
                html = "ERROR"    
        except urlfetch.DownloadError:
            html = None
        html = "WHO CARES"            
    elif log_type == "2":
        logging.info("logging with queue")
        t = Task(params=logging_params,method='GET')
        t.add('async-log-queue-%02d'%(random.randint(0,9)+1))
    elif log_type == "3":    
        logging.info("logging sync")
        logging_params.update(add_inst=True)
        log(**logging_params)        
        html = "LOGGED"
    

class EventOne(webapp.RequestHandler):
    def get(self):
        # self.response.headers['Content-Type'] = 'text/plain'
        uid = self.request.get("uid",None)
        dim_two_level_one = self.request.get("id",None)
        
        num_creatives = int(self.request.get("nc",1000))
        req = self.request.get("req","0")
        inst = self.request.get("inst","0")
        
        return_dim1l1 = not bool(int(self.request.get("fail",0)))
        
        # logging.info("instance_id: %s"%instance_id)
        t = time.time()
        
        request_id = "%s:%s:%s"%(t,uid,dim_two_level_one)
        
        # 90 percent of the time we attach information to the request
        if return_dim1l1 and random.randint(1,9) != 0:
            # level3:level2:level1
            if num_creatives > 1:
                maximum = round(pow(num_creatives,1.0/3.0)) - 1
                dim_one_level_one_key_name = "k:%s:%s:%s"%(random.randint(0,maximum),random.randint(0,maximum),random.randint(0,maximum)) 
            else:
                dim_one_level_one_key_name = "k:01:01:01"    
            dim_one_level_one = str(DimensionOneLevelOne.key_from_key_name(dim_one_level_one_key_name))
        else:
            dim_one_level_one_key_name = None
            dim_one_level_one = None
                
        
        logging_params = {"uid":uid,"dim2l1":dim_two_level_one,"t":t,"req":req,"inst":inst}
        if dim_one_level_one:
            imp_id = request_id + ":" + str(dim_one_level_one)
            logging_params.update(dim1l1=dim_one_level_one,imp=imp_id)
        
        log_type = self.request.get("log","0")
        event_log(log_type,logging_params)
        
        self.response.out.write(dim_one_level_one or 'None')    
        # self.response.out.write('<html><head/><body><b>Hello, webapp World! %s %s %s %s <br/> %s <br/> %s </b></body></html>'%(request_id,dim_two_level_one,uid,t,logging_params, html))
        

class EventTwo(webapp.RequestHandler):
    def get(self):        
        uid = self.request.get("uid",None)
        dim2l1 = self.request.get("dim2l1",None) # adunit
        dim1l1 = self.request.get("dim1l1",None) # creative
        appid = self.request.get("appid",None)
        t = time.time()
        
        logging_params = {"uid":uid,
                          "dim1l1":dim1l1,
                          "dim2l1":dim2l1,
                          "appid":appid,
                          "t":t,
                          "clk":t}
        
        #add clicks to user
        def add_click(udid,adunit,creative,time,appid):
            user = MobileUser.get_by_udid(udid)
            if not user:
                user = MobileUser(udid=udid)
            user.add_click(adunit,creative,time,appid)
            user.put()
        db.run_in_transaction(add_click,uid,dim2l1,dim1l1,t,appid)
        
        
        log_type = self.request.get("log","0")
        event_log(log_type,logging_params)
        

        self.response.out.write('click')    
        
class EventThree(webapp.RequestHandler):
    def get(self):
        appid = self.request.get("appid",None)
        uid = self.request.get("uid",None)
        t = time.time()
        
        
        def add_app(udid,appid):
            user = MobileUser.get_by_udid(udid)
            if not user:
                user = MobileUser(udid=udid)
            conversion = user.add_app(appid)
            logging.info(user.apps)
            user.put()
            return conversion

        adunit,creative = db.run_in_transaction(add_app,uid,appid)
        
        if bool(adunit):
            logging_params = {"uid":uid,
                              "dim1l1":creative,
                              "dim2l1":adunit,
                              "appid":appid,
                              "t":t,
                              "conv":t}        
                          
            log_type = self.request.get("log","0")
            event_log(log_type,logging_params)
        
        self.response.out.write("%s"%bool(adunit))

application = webapp.WSGIApplication([('/event/one', EventOne), #requests
                                      ('/event/two', EventTwo), #clicks
                                      ('/event/three',EventThree), #app-opens
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)
if __name__ == "__main__":
    main()
    
