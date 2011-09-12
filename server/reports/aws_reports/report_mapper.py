#!/usr/bin/python
import sys
from datetime import datetime
import logging

sys.path.append('.')


from parse_utils import gen_days, parse_line, build_keys


def main():
    for line in sys.stdin:
        line_dict = parse_line(line)
        for key in build_keys(line_dict, D1, D2, D3):
            print "%s\t%s" % (key, line_dict['vals'])

if __name__ == '__main__':
    main()


def mapper_test(line, d1, d2, d3):
    line_dict = parse_line(line)
    for key in build_keys(line_dict, d1, d2, d3):
        yield '%s\t%s' % (key,line_dict['vals'])

def reduce_test(key, values):
    values = [eval(value) for value in values]
    yield "%s\t%s" % (key, map(sum, zip(*values)))
