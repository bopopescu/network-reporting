import re
import reporting.models as reporting_models


def get_country_code(request=None,user_agent=None,locale=None):
    country_code = None
    
    split_pat = re.compile('[\-_]') # splits on '-' or '_'
    
    if request:
        locale = request.headers.get("Accept-Language")

    if locale:    
        try:
            country_code = re.split(split_pat,locale)[1].upper()
        except:
            pass    

    if user_agent:        
        country_code = None
        pat = re.compile(r'Mac OS X.*; ([^\)]{5})') # Match the first 5 characters that aren't the ending parenthesis
        match = pat.search(user_agent)
        if match:
            try:
                country_code = re.split(split_pat,match.group(1))[1].upper()
            except:
                pass
        else:
            pat = re.compile(r'Android.*; (.*?);')
            match = pat.search(user_agent)
            if match:
                try:
                    country_code = re.split(split_pat,match.group(1))[1].upper()
                except:
                    pass

    if not country_code:
        country_code = reporting_models.DEFAULT_COUNTRY
    return country_code         
    