#!/bin/sh

rm -frR .coverage

export DEBUG=1

rm -frR reports
mkdir reports

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_utils.py

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_file_io.py

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_init.py

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_main.py

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_yaml_helpers.py

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_http_requests_io.py

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_helper_init.py

echo ; echo ; echo "########################################################################################################################"
coverage run -a tests/test_models.py

echo ; echo ; echo "########################################################################################################################"
coverage report --omit="tests/test*" -m
coverage html -d reports --omit="tests/test*","/tmp/test_manifest_classes/*"
coverage report --format=markdown --omit="tests/test*","/tmp/test_manifest_classes/*" > doc/coverage/README.md
echo "Report available in file://$PWD/reports/index.html"
