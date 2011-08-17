#!/usr/bin/python
import sys
from datetime import datetime
import logging

sys.path.append('.')


from parse_utils import gen_days, parse_line, build_keys
D1 = 'week'
D2 = 'kw'
D3 = 'country'


def main():
    for line in sys.stdin:
        line_dict = parse_line(line)
        for key in build_keys(line_dict, D1, D2, D3):
            print "%s\t%s" % (key, line_dict['vals'])

if __name__ == '__main__':
    main()

