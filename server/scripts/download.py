#!/usr/bin/env python
# encoding: utf-8
"""
download.py

Created by Nafis Jamal on 2012-02-22.
Copyright (c) 2012 mopub, inc. All rights reserved.
"""

import sys
import os
import subprocess

def main():
    f = open('/Users/nafis/Desktop/kinds.txt')

    download_template = "time echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=%s --filename=/tmp/%s.data --email=olp@mopub.com --passin"

    for kind in f:
        kind = kind.strip()
        if not '#' in kind:
            print download_template % (kind, kind.lower())
            # subprocess.call([download_template % (kind, i)])

if __name__ == '__main__':
    main()

