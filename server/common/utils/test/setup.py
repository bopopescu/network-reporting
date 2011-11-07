import sys, os
if not os.path.exists('/home/ubuntu/'):
    sys.path.append(os.environ['PWD'])
from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()
