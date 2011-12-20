#!/bin/sh

# Check login credentials tests
echo Check Login Credentials Tests
echo
echo SETUP: Make sure selenium and chromedriver are installed
echo
nosetests --match='(?:^|[\b_\./-])mptest'
