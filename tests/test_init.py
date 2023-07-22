"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus import *

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))

class TestFunctionParseRawYamlData(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_basic_yaml(self):
        yaml_string = """
---
test: true
description: |
  This is a multi line
  test message
"""
        result = parse_raw_yaml_data(yaml_data=yaml_string)['part_1']
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertTrue('test' in result)
        self.assertTrue('description' in result)
        self.assertIsInstance(result['test'], bool)
        self.assertIsInstance(result['description'], str)
        self.assertTrue(result['test'])
        self.assertTrue('multi line' in result['description'])
        self.assertTrue('test message' in result['description'])

    def test_custom_tags_yaml_01(self):
        yaml_string = """---
AWSTemplateFormatVersion: "2010-09-09"

Parameters:

  RootDomainName:
    Type: String
    Default: example.tld

Resources:

  DNS: 
    Type: "AWS::Route53::HostedZone"
    Properties: 
      HostedZoneConfig: 
        Comment: !Sub "Deployed in account ${}AWS::AccountId{} in region ${}AWS::Region{}"
      Name: !Ref RootDomainName
""".format('{', '}', '{', '}')
        
        pre_result = None
        try:
            pre_result = parse_raw_yaml_data(yaml_data=yaml_string, use_custom_parser_for_custom_tags=True)
        except:
            pass
        self.assertIsNotNone(pre_result)
        self.assertIsInstance(pre_result, dict)
        result = dict()
        if 'part_1' in pre_result:
            result = pre_result['part_1']
        print('test_custom_tags_yaml_01(): result: {}'.format(json.dumps(result, default=str)))
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)

    def test_custom_tags_yaml_02(self):
        yaml_string = """---
AWSTemplateFormatVersion: "2010-09-09"

Parameters:

  RootDomainName:
    Type: String
    Default: example.tld

Resources:

  DNS: 
    Type: "AWS::Route53::HostedZone"
    Properties: 
      HostedZoneConfig: 
        Comment:
          Fn::Sub:
          - 'Deployed in account ${}AccountId{} in region ${}Region{}'
          - AccountId:
              Ref: AWS::AccountId
            Region:
              Ref: AWS::Region
      Name: 
        Ref: RootDomainName
""".format('{', '}', '{', '}')
        pre_result = parse_raw_yaml_data(yaml_data=yaml_string)
        self.assertIsNotNone(pre_result)
        self.assertIsInstance(pre_result, dict)
        result = dict()
        if 'part_1' in pre_result:
            result = pre_result['part_1']
        print('test_custom_tags_yaml_02(): result: {}'.format(json.dumps(result, default=str)))
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)

    def test_custom_tags_yaml_03(self):
        yaml_string = """---
AWSTemplateFormatVersion: "2010-09-09"

Parameters:

  RootDomainName:
    Type: String
    Default: example.tld

Resources:

  DNS: 
    Type: "AWS::Route53::HostedZone"
    Properties: 
      HostedZoneConfig: 
        Comment: !Sub "Deployed in account ${}AWS::AccountId{} in region ${}AWS::Region{}"
      Name: !Ref RootDomainName
""".format('{', '}', '{', '}')
        
        pre_result = None
        try:
            pre_result = parse_raw_yaml_data(yaml_data=yaml_string)
        except:
            pass
        self.assertIsNotNone(pre_result)
        self.assertIsInstance(pre_result, dict)
        result = dict()
        if 'part_1' in pre_result:
            result = pre_result['part_1']
        print('test_custom_tags_yaml_01(): result: {}'.format(json.dumps(result, default=str)))
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)


if __name__ == '__main__':
    unittest.main()
