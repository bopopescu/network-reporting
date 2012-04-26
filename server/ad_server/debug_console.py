import datetime
import logging
from common.utils import simplejson

# singleton debug console
class DebugConsole(object):
    log_levels = [logging.info]
    
    def __init__(self, request=None, response=None):
        self.request = request
        self.response = response
        self.lines = []
        self.rendered_creative = None
        self.log_to_console = False
        
    def start(self, log_to_console=False):
        self.lines = []    
        self.log_to_console = log_to_console
        
    def info(self, logline):
        self.log(logline, logging.info)
    
    def debug(self, logline):
        self.log(logline, logging.debug)
    
    def warning(self, logline):
        self.log(logline, logging.warning)
    
    def error(self, logline):                
        self.log(logline, logging.error)
        
    def critical(self, logline):
        self.log(logline, logging.critical)    
        
    def log(self, logline, logging_type=logging.info):
        "prepend time"
        # logline = "%s - %s" % (datetime.datetime.now(), logline)
        # log to the console just as before if set to
        if self.log_to_console:
            logging_type(logline)
        if logging_type in self.log_levels:
            self.lines.append(logline)

    def render(self):
        self.response.out.write("""<html>
    <head>
        <style type="text/css">
            body{padding:0;margin:0;}
            .line{width:100%%; word-wrap:break-word;}
        </style>
        <script type="text/javascript">
            var total_lines = %(num_lines)s;
            var current_line = 0;
            var logRevealInterval = 20;
            
            function scrollBottom(dist){
                //window.scrollTo(0,document.body.scrollHeight);
                //window.location = '#bottom';
                window.scrollBy(0,dist)
            }
            
            function showLine(){
                var line = document.getElementById('line_'+current_line.toString());
                console.log(line);
                line.style.display = 'block';
                scrollBottom(line.offsetHeight);
                current_line++;
                if (current_line < total_lines){
                    setTimeout("showLine()",logRevealInterval);
                }
                else{
                    setTimeout("showCreative()",logRevealInterval);
                }
            }
            
            function showCreative(){
                var creative = document.getElementById('creative');
                creative.style.display = 'block';
                scrollBottom(creative.offsetHeight);
            }
            
            window.onload = function(){
                setTimeout("showLine()",logRevealInterval);
            }
            
        </script>
    </head>
    <body style="width:100%%;">"""%dict(num_lines=len(self.lines)))
        # self.response.out.write('<div style="height:350px;overflow:auto">')
        for i,line in enumerate(self.lines):
            self.response.out.write('<div class="line" id="line_%d" style="display:none;">%s</div>'%(i,line))

        # self.response.out.write('</div>')
        if self.rendered_creative:
            self.response.out.write('\n<br/>\n<iframe id="creative" width="320px" height="50px" frameBorder="0" scrolling="no" style="display:none;"></iframe>')
            javascript = """
<div id="replace" style="display:none;"><style>body{padding:0;margin:0;}</style>%s</div>            
<script type='text/javascript'>
    var s = document.getElementById('creative');
    var replace = document.getElementById('replace')
    s.contentDocument.write(replace.innerHTML);
    replace.parentNode.removeChild(replace);
    window.onload(); // manually calling onload
</script>
"""%self.rendered_creative
            self.response.out.write(javascript)
        self.response.out.write('<div style="height:10px"></div><a id="bottom"></a></body></html>')    
        
trace_logging = DebugConsole()
