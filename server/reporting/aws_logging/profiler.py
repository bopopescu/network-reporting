import cgi
import os 
import re
import sys
import traceback
import urlparse
from optparse import OptionParser

from wurfl import devices
from pywurfl.algorithms import TwoStepAnalysis

from parse_utils import parse_logline



def parse(logline, search_algo):
    d = parse_logline(logline)
    if d:        
        info = d['user_agent']
        # ua_device = re.search(r'\(.*?\)', d['client']).group()
        
        if len(info) != 0:
            return info['blurb'], '\t'.join(['brand_name='+info['brand_name'], 'marketing_name='+info['marketing_name'], 'device_os='+info['device_os'], 'os_version='+info['device_os_version']])
        
    return None, None        
    
    
def main():
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()

    search_algo = TwoStepAnalysis(devices)

    with open(options.input_file, 'r') as f:
        with open('debug.' + options.input_file, 'w') as debug_f:
            for line in f:
                blurb, result = parse(line, search_algo)
                if result:
                    debug_f.write(blurb+'\n')
                    debug_f.write(result+'\n\n')
            
                

if __name__ == '__main__':
    main()

    
    