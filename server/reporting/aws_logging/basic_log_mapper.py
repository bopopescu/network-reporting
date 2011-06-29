#!/usr/bin/python
import sys
from datetime import datetime

# for EMR so imported modules can be found within each task
sys.path.append('.')

import utils
from parse_utils import parse_logline


# return format:
# k:adunit_id:creative_id:country_code:time, [req_count, imp_count, clk_count, conv_count]
def format_kv_pair(handler, param_dict, country_code, date_hour):    
    if handler == utils.AD:
        return 'k:%s:%s:%s:%s' % (param_dict.get('id'), '', country_code, date_hour), '[1, 0, 0, 0]'
    if handler == utils.IMP:
        return 'k:%s:%s:%s:%s' % (param_dict.get('id'), param_dict.get('cid'), country_code, date_hour), '[0, 1, 0, 0]'
    if handler == utils.CLK:
        return 'k:%s:%s:%s:%s' % (param_dict.get('id'), param_dict.get('cid'), country_code, date_hour), '[0, 0, 1, 0]'
    if handler == utils.REQ:
        return 'k:%s:%s:%s:%s' % (param_dict.get('id'), param_dict.get('cid'), country_code, date_hour), '[1, 0, 0, 0]'
    return None, None
        
    
# abstract out core logic on parsing on handler params; this function is used for both mrjob (local testing) and boto (remote EMR job)
def generate_kv_pairs(line):
    logline_dict = parse_logline(line)

    if logline_dict:
        handler = logline_dict.get('path')
        param_dict = logline_dict.get('params')
        country_code = logline_dict.get('country_code')

        # ex: 14/Mar/2011:15:04:09 -0700
        log_date = logline_dict.get('date', None)
        log_time = logline_dict.get('time', None)

        if None not in [handler, param_dict, country_code, log_date, log_time]:
            try:
                # construct datetime object           
                date_hour = datetime.strptime(log_date + ':' + log_time, '%d/%b/%Y:%H:%M:%S')

                # resolution is hour
                hour_k, hour_v = format_kv_pair(handler, param_dict, country_code, date_hour.strftime('%y%m%d%H'))
                # resolution is day
                date_k, date_v = format_kv_pair(handler, param_dict, country_code, date_hour.strftime('%y%m%d'))

                if hour_k and 'None' not in hour_k and date_k and 'None' not in date_k:
                    return hour_k, hour_v, date_k, date_v
            except:
                return None, None, None, None            
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
