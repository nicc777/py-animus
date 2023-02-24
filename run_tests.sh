#!/bin/sh

export DEBUG=1

rm -frR reports
mkdir reports


echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_plugins.py

echo ; echo ; echo "########################################################################################################################"
coverage report --omit="tests/test*" -m
coverage html -d reports --omit="tests/test*"
coverage report --format=markdown --omit="tests/test*" > doc/coverage/README.md
echo "Report available in file://$PWD/reports/index.html"

