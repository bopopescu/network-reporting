#!/usr/bin/python
import sys
from datetime import datetime

# for EMR so log_parser can be found within each task
sys.path.append('.')

from log_parser import parse_logline, AD, IMP, CLK, REQ



def format_kv_pair(handler, param_dict, date_hour):
    # return format:
    # k:adunit_id:creative_id:time, [req_count, imp_count, clk_count, conv_count, user_count]
    
    if handler == AD:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), '', date_hour), '[1, 0, 0, 0]'         
    if handler == IMP:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), param_dict.get('cid', None), date_hour), '[0, 1, 0, 0]'         
    if handler == CLK:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), param_dict.get('cid', None), date_hour), '[0, 0, 1, 0]'
    if handler == REQ:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), param_dict.get('cid', None), date_hour), '[1, 0, 0, 0]'
    return None, None
        
    
# abstract out core logic on parsing on handler params; this function is used for both mrjob (local testing) and boto (remote EMR job)
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
            hour_k, hour_v = format_kv_pair(handler, param_dict, date_hour.strftime('%y%m%d%H'))
            # resolution is day
            date_k, date_v = format_kv_pair(handler, param_dict, date_hour.strftime('%y%m%d'))

            if hour_k and 'None' not in hour_k and date_k and 'None' not in date_k:
                return hour_k, hour_v, date_k, date_v
    return None, None, None, None
                


def main():
    try:
        for line in sys.stdin:
            hour_k, hour_v, date_k, date_v = generate_kv_pairs(line)
            if hour_k and hour_v and date_k and date_v:
                print "%s\t%s" % (hour_k, hour_v)
                print "%s\t%s" % (date_k, date_v)
    except:
        pass


if __name__ == '__main__':
    main()
