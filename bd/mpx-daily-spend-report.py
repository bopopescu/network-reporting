#!/usr/bin/env python2.7
# encoding: utf-8
"""
mpx-daily-spent.py

Created by Jim Payne on 2011-12-10.
"""

import sys
import os
import datetime
import json
import urllib

def main():
    mpx = json.loads(urllib.urlopen("http://mpx.mopub.com/spent").read())
    
    total = sum([x["spent"] for x in mpx.values()])
    
    a=[(x["bidder_name"], x["spent"]) for x in mpx.values() if x["spent"] > 0]
    a.sort(lambda x,y: cmp(y[1],x[1]))
    
    print("Total Spend: $%.2f\n" % total)
    print("Top Bidders\n===========")
    for x in a:
        print "%s: $%.2f" % (x[0], x[1])
        
    print("\nData retrieved at %s" % datetime.datetime.now())

if __name__ == '__main__':
    main()

