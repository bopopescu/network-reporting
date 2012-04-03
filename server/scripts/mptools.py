#!/usr/bin/env python

def main(*args, **kwargs):
    print args
    print kwargs

if __name__ == '__main__':
    import sys
    main(sys.args)