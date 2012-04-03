import subprocess
import base64
import simplejson
from django.conf import settings

def track(event, properties=None):
    """
    A simple function for asynchronously logging to the mixpanel.com API.
    This function requires `curl` and Python version 2.4 or higher.

    @param event: The overall event/category you would like to log this data under
    @param properties: A dictionary of key-value pairs that describe the event
                       See http://mixpanel.com/api/ for further detail.
    @return Instance of L{subprocess.Popen}
    
    Example usage:
    track("invite-friends",
    {"method": "email", "number-friends": "12", "ip": "123.123.123.123"})
    """
    if properties == None:
        properties = {}
    
    # XXX: Be sure to change this!
    token = settings.MIXPANEL_API_TOKEN
    
    if "token" not in properties:
        properties["token"] = token

    params = {"event": event, "properties": properties}
    data = base64.b64encode(simplejson.dumps(params))
    request = "http://api.mixpanel.com/track/?data=" + data
    return subprocess.Popen(("curl",request), stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)