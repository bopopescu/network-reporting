#!/bin/bash
pushd ..
touch server/__init__.py
pylint --rcfile=".pylintrc" --init-hook="import sys; sys.path.append('$VIRTUAL_ENV/lib/python2.7/site-packages'); sys.path.append('$PWD/optimizer')" -f parseable --reports=no --ignore=common,boto,mapreduce,djangoflash,reporting,aws_reporting,appengine_console.py,migrater.py,appengine_config.py,ad_server,admin/beatbox,scripts,reports/aws_reports,account,appengine_django server
rm -rf server/__init__.py*
popd
