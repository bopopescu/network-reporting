#!/usr/bin/python
import sys
from datetime import datetime
import logging

sys.path.append('.')


from reports.aws_reports.parse_utils import gen_days, parse_line, build_keys


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

MAPPER_P1 = """#!/usr/bin/python
import sys
from datetime import datetime
import logging

DIM1 = "%(dim1)s"
DIM2 = "%(dim2)s"
DIM3 = "%(dim3)s"
START = "%(start)s"
END = "%(end)s"

if DIM2 == 'None':
    DIM2 = None

if DIM3 == 'None':
    DIM3 = None

START = datetime.strptime(START, '%%y%%m%%d')
END = datetime.strptime(END, '%%y%%m%%d')
"""
MAPPER_P2 = """
sys.path.append('.')

from parse_utils import gen_days, parse_line, build_keys

def main():
    for line in sys.stdin:
        line_dict = parse_line(line)
        date = line_dict['time'].date()
        if not (date <= END.date() and date >= START.date()):
            continue
        for key in build_keys(line_dict, DIM1, DIM2, DIM3):
            print "%s\\t%s" % (key, line_dict['vals'])

if __name__ == '__main__':
    main()


def mapper_test(line, d1, d2, d3):
    line_dict = parse_line(line)
    for key in build_keys(line_dict, d1, d2, d3):
        yield '%s\\t%s' % (key,line_dict['vals'])

def reduce_test(key, values):
    values = [eval(value) for value in values]
    yield "%s\\t%s" % (key, map(sum, zip(*values)))
"""
