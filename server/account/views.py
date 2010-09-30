import logging, os, re, datetime, hashlib

from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response, JSONResponse

from common.utils.decorators import whitelist_login_required

# from common.ragendja.auth.decorators import google_login_required as login_required

from account.models import Account

class RequestHandler(object):
    def __call__(self,request,*args,**kwargs):
        self.params = request.POST or request.GET
        self.request = request
        self.account = None
        user = users.get_current_user()
        if user:
          if users.is_current_user_admin():
            account_key_name = request.COOKIES.get("account_impersonation",None)
            if account_key_name:
              self.account = Account.get_by_key_name(account_key_name)
        if not self.account:  
          self.account = Account.current_account()
          
        if request.method == "GET":
            return self.get(*args,**kwargs)
        elif request.method == "POST":
            return self.post(*args,**kwargs)    
    def get(self):
        pass
    def put(self):
        pass

class AccountHandler(RequestHandler):
  def get(self):
    return render_to_response(self.request,'account/account.html', {'account': self.account})

  def post(self):
    a = self.account
    a.adsense_pub_id = self.request.POST.get("adsense_pub_id")
    a.admob_pub_id = self.request.POST.get("admob_pub_id")
    a.put()
    return HttpResponseRedirect("/account")

@whitelist_login_required     
def index(request,*args,**kwargs):
  return AccountHandler()(request,*args,**kwargs)     

class LogoutHandler(RequestHandler):
  def get(self):
    return HttpResponseRedirect(users.create_logout_url('/main/'))
    
def logout(request,*args,**kwargs):
  return LogoutHandler()(request,*args,**kwargs)
  
def test(request,*args,**kwargs):
  import time
  time.sleep(2)
  html = """<html> 
  	<head>
  		<title></title>
  	</head> 
  	<body style="margin: 0;width:320px;height:480px;" > 
    	<script>
  		  function finishLoad(){window.location="mopub://finishLoad";} 
  		  window.onload = function(){
  		    finishLoad();
  		  }
  		</script>
  		<script type="text/javascript">
  			function webviewDidClose(){var img = new Image(); img.src="/hellothereimclosing/"} 
  			function webviewDidAppear(){var img = new Image(); img.src="/hellothereimopening/"} 
        function showImage(){var img = document.createElement("img"); img.setAttribute('src','/images/yelp.png'); document.body.appendChild(img);}
        setTimeout("showImage()",100);
  			function close(){window.location = "mopub://close"};
  			//setTimeout("close()",10000);
  		</script>
  	</body>
  </html>
  """
  response = HttpResponse(html) 
  # response['X-Closebutton'] = 'Next'
  return response

def test2(request,*args,**kwargs):
  raise Http404
  html = """<html> 
  	<head>
  		<title></title>
  	</head> 
  	<body style="margin: 0;width:320px;height:480px;" > 
  		<script type="text/javascript">
  			function webviewDidClose(){var img = new Image(); img.src="/hellothereimclosing/"} 
  			function webviewDidAppear(){var img = new Image(); img.src="/hellothereimopening/"} 
  			function close(){window.location="mopub://finishLoad?query=imthequery";} 
  			setTimeout("finish()",5000);

  			function showImage(){var img = document.createElement("img"); img.setAttribute('src','/images/yelp.png'); document.body.appendChild(img);}
  			setTimeout("showImage()",3000);
  		</script>
  	</body>
  </html>
  """
  response = HttpResponse(html) 
  response['X-CloseButton'] = 'None'
  return response  
  
  
  
  
# <script> function  finishLoad(){window.location="mopub://finishLoad";} window.onload =  function(){ finishLoad(); }  </script> <script type="text/javascript">  function webviewDidClose(){var img  = new Image();  img.src="/hellothereimclosing/"}  function  webviewDidAppear(){var  img  =  new   Image();  img.src="/hellothereimopening/"}  function  showImage(){var  img  =  document.createElement("img"); img.setAttribute('src','/images/yelp.png'); document.body.appendChild(img);} setTimeout("showImage()",100); function  close(){window.location = "mopub://done"}; //setTimeout("close()",10000); </script>