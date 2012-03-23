import re

MAX_IPS = 5
COMBINED_LOGLINE_PAT = re.compile(r'(?P<origin>\d+\.\d+\.\d+\.\d+) '
    + r'(?P<identd>-|\w*) (?P<auth>-|\w*) '
    + r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '
    + r'"(?P<method>\w+) (?P<url>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+) '
    + r'(?P<referrer>-|"[^"]*") (?P<client>"[^"]*")')
    
COUNTRY_RE = r'([a-zA-Z][a-zA-Z])[-_](?P<ccode>[a-zA-Z][a-zA-Z])'

country_ip_dict = {}
    
with open('/Users/nafis/Desktop/request-logfile') as f:
    for logline in f:
        m = COMBINED_LOGLINE_PAT.match(logline)
        if m:
            d = m.groupdict()
            ip = d.get('origin')
            user_agent = d.get('client')
            
            countries = re.findall(COUNTRY_RE, user_agent)
            if len(countries) == 1:
                country = countries[0][0].upper()
                lang = countries[0][1].lower()
                if not country in country_ip_dict:
                    country_ip_dict[country] = ('%s-%s'%(lang,country),ip)
print country_ip_dict
for key,value in country_ip_dict.iteritems():
 print "'%s': %s"%(key,value)
