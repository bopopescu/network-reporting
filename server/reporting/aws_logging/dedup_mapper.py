#!/usr/bin/python
import sys

def main():
    try:
        for line in sys.stdin:
            line = line.strip() # get rid of \n at the end
            print "LongValueSum:%s\t%i" % (line, 1)
    except:
        pass


if __name__ == '__main__':
    main()
