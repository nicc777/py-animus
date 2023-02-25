#!/bin/sh

export DEBUG=1

rm -frR reports
mkdir reports

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_manifest_management.py

echo ; echo ; echo "########################################################################################################################"
coverage report --omit="tests/test*" -m
coverage html -d reports --omit="tests/test*","/tmp/test_manifest_classes/*"
coverage report --format=markdown --omit="tests/test*","/tmp/test_manifest_classes/*" > doc/coverage/README.md
echo "Report available in file://$PWD/reports/index.html"
