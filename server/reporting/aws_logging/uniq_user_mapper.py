#!/usr/bin/python
import sys
from datetime import datetime


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
    param_dict = {}
    fields = line.strip().split(',')
    for f in fields:
        pair = f.split('=')
        if len(pair) != 2: continue
        param_dict[pair[0]] = pair[1]
        
    handler = param_dict.get('handler', None)

    # ex: 14/Mar/2011:15:04:09 -0700
    log_date = param_dict.get('date', None)
    log_time = param_dict.get('time', None)
        
    if handler and log_date and log_time:
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
        # read in output from preprocess stage; key is comma-separated preprocessed log line, ignore the value
        for line in sys.stdin:
            parts = line.split('\t')
            if len(parts) != 2: continue
            
            line = parts[0]
            for key, value in generate_kv_pairs(line):
                if key and value:
                    print "%s\t%s" % (key, value)
    except:
        pass


if __name__ == '__main__':
    main()
