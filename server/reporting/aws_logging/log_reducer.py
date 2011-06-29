#!/usr/bin/python
import sys
import traceback

table = {}

def parse_and_update_table(line):
    key, counts = line.split('\t', 1)
    counts = eval(counts)
    if key in table:
        table[key] = update_counts(table[key], counts)
    else:
        table[key] = counts


def update_counts(current, delta):
    return map(sum, zip(current, delta))


def main():
    for line in sys.stdin:
        try:
            parse_and_update_table(line)
        except:
            traceback.print_exc()
        
    for key, counts in table.iteritems():
        try:
            print "%s\t%s" % (key, str(counts))
        except:
            traceback.print_exc()
        

if __name__ == '__main__':
    main()
