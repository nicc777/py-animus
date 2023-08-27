"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""


import os
import yaml
import json


class ValueTag(yaml.YAMLObject):
    yaml_tag = u'!Value'

    def __init__(self, txt_var):
        self.txt_var_original = txt_var
        self.txt_var_converted = txt_var.upper()

    def __repr__(self):
        return self.txt_var_converted

    @classmethod
    def from_yaml(cls, loader, node):
        return ValueTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.txt_var_original)
