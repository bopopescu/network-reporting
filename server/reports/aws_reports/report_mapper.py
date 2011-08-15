#!/usr/bin/python
import sys
from datetime import datetime

sys.path.append('.')


from parse_utils import gen_days, parse_line, build_keys


def main(args):
    d1, d2, d3, start, end = args
    for line in sys.stdin:
        days = gen_days(start, end, True)
        line_dict = parse_line(line)
        for key in build_keys(line_dict, d1, d2, d3):
            print "%s\t%s" % (key, line_dict['vals'])

if __name__ == '__main__':
    main(sys.argv[1:])

