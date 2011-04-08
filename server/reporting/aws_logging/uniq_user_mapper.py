#!/usr/bin/python
import sys
from datetime import datetime

# for EMR so log_parser can be found within each task
sys.path.append('.')

from log_parser import parse_logline

PUB_PARAMS = ['adunit', 'app', '']
ADV_PARAMS = ['creative', 'adgroup', 'campaign', '']


# generator return format:
# k:handler:acount:pub:adv:time, uniq_user_count
def generate_pub_adv_combos(handler, param_dict, date_hour):
    for pub_param in PUB_PARAMS:
        for adv_param in ADV_PARAMS:
            if 'udid' in param_dict and 'account' in param_dict:
                udid = param_dict['udid']
                account = param_dict['account']
                pub = param_dict.get(pub_param, None)
                adv = param_dict.get(adv_param, None)
                yield 'UniqValueCount:k:%s:%s:%s:%s:%s' % (handler, account, pub or '', adv or '', date_hour), udid
                # remove handler to calculate uniq users across all handlers
                yield 'UniqValueCount:k:%s:%s:%s:%s:%s' % ('', account, pub or '', adv or '', date_hour), udid
            yield None, None
           
    
# abstract out core logic; this function is used for both mrjob (local testing) and boto (remote EMR job)
def generate_kv_pairs(line):
    logline_dict = parse_logline(line)
    if logline_dict:
        handler = logline_dict.get('path', None)
        param_dict = logline_dict.get('params', None)

        # ex: 14/Mar/2011:15:04:09 -0700
        log_date = logline_dict.get('date', None)
        log_time = logline_dict.get('time', None)
        # log_tz = logline_dict.get('tz', None)
            
        if handler and param_dict and log_date and log_time:# and log_tz:      
            # construct datetime object           
            date_hour = datetime.strptime(log_date + ':' + log_time, '%d/%b/%Y:%H:%M:%S')
            
            # resolution is hour            
            for key, value in generate_pub_adv_combos(handler, param_dict, date_hour.strftime('%y%m%d%H')):
                yield key, value

            # resolution is day                
            for key, value in generate_pub_adv_combos(handler, param_dict, date_hour.strftime('%y%m%d')):
                yield key, value
    yield None, None


def main():
    try:
        for line in sys.stdin:
            for key, value in generate_kv_pairs(line):
                if key and value:
                    print "%s\t%s" % (key, value)
    except:
        pass


if __name__ == '__main__':
    main()
