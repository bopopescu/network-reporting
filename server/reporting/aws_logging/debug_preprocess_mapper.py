import preprocess_mapper 

import os
import sys
import time
import traceback
import logging

from datetime import datetime
from optparse import OptionParser


def main():
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n')
        
    with open(options.input_file) as f:
        for line in f:
            parts = line.split('\t')
            if len(parts) != 2: continue
            
            line = parts[0] 
            try:
                pp_line = preprocess_mapper.preprocess_logline(line)
                # if not pp_line:
                #     print line
            except:
                print line
                print
                traceback.print_exc()
            
if __name__ == '__main__':
    main()
