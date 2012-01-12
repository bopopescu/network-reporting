#!/usr/bin/env python
from subprocess import call

ADSERVER_APP_YAML_FILENAME = 'app.adserver.yaml'
FRONTEND_APP_YAML_FILENAME = 'app.frontend.yaml'
APP_YAML_FILENAME = 'app.yaml'

app_yaml_file = open(APP_YAML_FILENAME, 'r')
original_app_yaml_contents = app_yaml_file.read()
app_yaml_file.close()

adserver_app_yaml_file = open(ADSERVER_APP_YAML_FILENAME)
adserver_app_yaml_contents = adserver_app_yaml_file.read()
adserver_app_yaml_file.close()

# writes the 'adserver.app.yaml' contents to 'app.yaml'
print 'copying app.adserver.yaml -> app.yaml'
app_yaml_file = open(APP_YAML_FILENAME, 'w')
app_yaml_file.write(adserver_app_yaml_contents)
app_yaml_file.close()

# actually deploy
try:
    call(['appcfg.py', 'update', '.'])
# if we manually cancel we still want to tidy up
except KeyboardInterrupt: 
    pass

# return the original contents of app.yaml so git is happy
print 'Returning app.yaml'
app_yaml_file = open(APP_YAML_FILENAME, 'w')
app_yaml_file.write(original_app_yaml_contents)
app_yaml_file.close()
