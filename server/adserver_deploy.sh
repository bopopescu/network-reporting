#!/bin/bash
echo "copying 'app.adserver.yaml' -> 'app.yaml'"
cp app.adserver.yaml app.yaml
echo "uploading to GAE"
python2.5 appcfg.py update .
echo "copying 'app.frontend.yaml' -> 'app.yaml'"
# cp app.frontend.yaml app.yaml