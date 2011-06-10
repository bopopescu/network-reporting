
from common.constants import IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES

def get_os_version(user_agent_string):
    """ Returns the appropriate string for the os version """
    
    IOS_VERSIONS = [choice[0] for choice in IOS_VERSION_CHOICES]
    ANDROID_VERSIONS = [choice[0] for choice in ANDROID_VERSION_CHOICES]
    
    raise NotImplementedError
    
def get_os(user_agent_string):
    """ Returns 'iOS', 'android' or 'other' """
    raise NotImplementedError