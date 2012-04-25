rm /usr/local/bin/dev_appserver.pyc
nosetests-2.5 mytest.py --with-gae --gae-application='/Users/jcp/development/mopub/server' --without-sandbox
