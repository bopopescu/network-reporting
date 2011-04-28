import re
import reporting.models as reporting_models

# matches sequence: space, 2 char, - or _, 2 char, 0 or more ;, followed by char that's not a char, number, - or _
COUNTRY_PAT = re.compile(r' [a-zA-Z][a-zA-Z][-_](?P<ccode>[a-zA-Z][a-zA-Z]);*[^a-zA-Z0-9-_]')


def get_country_code(user_agent):
    m = COUNTRY_PAT.search(user_agent)
    if m:
        country_code = m.group('ccode')
        return country_code.upper()
    return reporting_models.DEFAULT_COUNTRY
    
def get_user_agent(request):
    return request.get('ua') or request.headers['User-Agent']    
    
def get_ip(request):
    return request.get('ip') or request.remote_addr