#!/usr/bin/python
import sys

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
    try:
        for line in sys.stdin:
            parse_and_update_table(line)
    except:
        pass
        
    for key, counts in table.iteritems():
        print "%s\t%s" % (key, str(counts))

if __name__ == '__main__':
    main()
