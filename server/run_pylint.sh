#!/bin/sh
pushd ..
pylint --rcfile=".pylintrc" --init-hook="import sys; sys.path.append('$VIRTUAL_ENV/lib/python2.7/site-packages'); sys.path.append('$PWD/optimizer')" -f parseable --reports=no `find . -name "*.py"` 2>&1 > pylint.txt
popd
