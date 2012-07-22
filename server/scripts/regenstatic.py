#! /usr/bin/env python

import os
from subprocess import call, check_output, CalledProcessError
PWD = os.path.dirname(__file__)

# See if they have juicer, and if not, install it.
try:
    user_has_juicer = check_output(['which', 'juicer']) != ''
except CalledProcessError:
    user_has_juicer = False

if not user_has_juicer:
    print 'Installing sass (sass-lang.org)...'
    call(['gem', 'install', 'juicer'])

# yui_compressor is a dependency for juicer that we need
# cant figure out how to get juicer to tell you what
# plugins are installed, so we dont bother to check first
call(['juicer', 'install', 'yui_compressor'])

# regenerate our plugins
call([
    'juicer',
    'merge',
    '-s',
    '-f',
    '-o',
    os.path.join(PWD,'../public/js/plugins.js'),
    os.path.join(PWD, '../public/js/libs/*.js'),
])

# regenerate our utilities
call([
    'juicer',
    'merge',
    '-s',
    '-f',
    '-o',
    os.path.join(PWD,'../public/js/mopub.js'),
    os.path.join(PWD,'../public/js/utility/*.js'),
])


# See if they have sass, and if not, install it.
try:
    user_has_sass = check_output(['which', 'sass']) != ''
except CalledProcessError:
    user_has_sass = False

if not user_has_sass:
    print 'Installing sass (sass-lang.org)...'
    call(['gem', 'install', 'sass'])

    
call([
    'sass',
    '--update',
    os.path.join(PWD,'../public/css/style.scss')
])