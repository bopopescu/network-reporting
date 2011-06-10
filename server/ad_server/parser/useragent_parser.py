
from common.constants import IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES

def get_os_version(user_agent_string):
    """ Returns the appropriate float for the os version """
    raise NotImplementedError
    
def get_os(user_agent_string):
    """ Returns 'iOS', 'android' or 'other' """
    raise NotImplementedError