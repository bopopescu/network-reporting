import datetime

from google.appengine.ext import webapp
from stats.log_service import logger
from common.utils.timezones import Pacific_tzinfo
from common.utils import helpers 

# COMBINED_LOGLINE_PAT = re.compile(r'(?P<origin>\d+\.\d+\.\d+\.\d+) '
#     + r'(?P<identd>-|\w*) (?P<auth>-|\w*) '
#     + r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '
#     + r'"(?P<method>\w+) (?P<url>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+) '
#     + r'(?P<referrer>-|"[^"]*") (?P<client>"[^"]*")')
# 78.136.56.162 - - [14/Jun/2011:11:50:54 -0700] "GET /m/open?v=3&udid=BE81EBBA9C52CF51D68BDB789832B850&id=352683833 HTTP/1.1" 200 147 - "gzip(gfe),gzip(gfe),gzip(gfe)" "ads.mopub.com" ms=78 cpu_ms=376 api_cpu_ms=329 cpm_usd=0.010488

class MPLoggingWSGIApplication(webapp.WSGIApplication):
    APACHE_STR_FORMAT = '%(ip)s %(identd)s %(auth_user)s [%(date)s] "%(method)s %(url)s %(protocol)s" %(status)s %(bytes)s %(referrer)s "%(user_agent)s"'

    def __init__(self, url_mapping, debug=False):
      """Initializes this application with the given URL mapping.

      Args:
        url_mapping: list of (URI regular expression, RequestHandler) pairs
                     (e.g., [('/', ReqHan)])
        debug: if true, we send Python stack traces to the browser on errors
      """
      self._init_url_mappings(url_mapping)
      self.__debug = debug


      MPLoggingWSGIApplication.active_instance = self
      self.current_request_args = ()
    
    def __call__(self, environ, start_response):
      """Called by WSGI when a request comes in."""
      request = self.REQUEST_CLASS(environ)
      response = self.RESPONSE_CLASS()


      MPLoggingWSGIApplication.active_instance = self


      handler = None
      groups = ()
      for regexp, handler_class in self._url_mapping:
        match = regexp.match(request.path)
        if match:
          handler = handler_class()


          handler.initialize(request, response)
          groups = match.groups()
          break


      self.current_request_args = groups


      if handler:
        try:
          method = environ['REQUEST_METHOD']
          if method == 'GET':
            handler.get(*groups)
          elif method == 'POST':
            handler.post(*groups)
          elif method == 'HEAD':
            handler.head(*groups)
          elif method == 'OPTIONS':
            handler.options(*groups)
          elif method == 'PUT':
            handler.put(*groups)
          elif method == 'DELETE':
            handler.delete(*groups)
          elif method == 'TRACE':
            handler.trace(*groups)
          else:
            handler.error(501)
        except Exception, e:
          handler.handle_exception(e, self.__debug)
      else:
        response.set_status(404)


      response.wsgi_write(start_response)
      
      # inserts a hook to do any sort of 
      # processing before the actual return
      self._call_hook(request, response)
      
      return ['']
    
    
    def _call_hook(self, request, response):
        self._log_request(request, response)
    
    def _log_request(self, request, response):
        apache_string = self._build_apache_string(request, response)
        logger.log(apache_string)

    def _build_apache_string(self, request, response):
        request_origin = request.remote_addr
        request_user =  request.remote_user
        request_method = request.method
        request_url = self._get_url_with_country(request)
        request_protocol = request.environ.get("SERVER_PROTOCOL")
        request_referrer = request.environ.get("HTTP_REFERER")
        request_user_agent = request.environ.get("HTTP_USER_AGENT")
        
        # gets data from the response
        response_status_code = response.status
        response_bytes = 10 # TODO: make this not hard coded
        response_datetime = datetime.datetime.now(Pacific_tzinfo())
        
        apache_dict = { 'ip': request_origin,
                        'identd': None,
                        'auth_user': request_user,
                        'date': response_datetime.strftime('%d/%b/%Y:%H:%M:%S %z'),#14/Jun/2011:11:50:54 -0700
                        'method': request_method,
                        'url': request_url,
                        'protocol': request_protocol,
                        'status': response_status_code,
                        'bytes': response_bytes,
                        'referrer': ('"%s"'%request_referrer) if request_referrer else None,
                        'user_agent': request_user_agent,
                      }
        
        # default all elements to '-' if doesn't exist
        for key, value in apache_dict.iteritems():
            apache_dict[key] = value or '-'
        
        return self.APACHE_STR_FORMAT % apache_dict
    
    def _get_url_with_country(self, request):
        return  request.path_qs + '&mpcountry=' + helpers.get_country_code(headers=request.headers)
