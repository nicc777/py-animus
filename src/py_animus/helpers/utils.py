"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import copy
import traceback
import random


class Field:

    def __init__(self, name: str, value: object=None):
        self.name = name
        self.children = list()
        self.value = value

    def to_dict(self):
        if self.value is None:
            return {self.name: None}
        elif self.value.__class__.__name__ == 'Field':
            return {self.name: self.value.to_dict()}
        return {self.name: self.value}


def create_field(dotted_name: str, value: object)->Field:
    field_names = dotted_name.split('.')
    if len(field_names) > 1:
        next_dotted_name = '.'.join(field_names[1:])
        field = Field(name=field_names[0], value=create_field(dotted_name=next_dotted_name, value=value))
    else:
        field = Field(name=field_names[0], value=copy.deepcopy(value))
    return field


def merge_dicts(A: dict, B: dict)->dict:
    # FROM https://stackoverflow.com/questions/29241228/how-can-i-merge-two-nested-dictionaries-together (Vivek Sable)
    for i, j in B.items(): 
        if i in A:
            A[i].update(j)
        else:
            A[i] = j
    return A


def generate_random_string(
    length: int=16,
    chars: str='abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
)->str:
    result = ''
    chars_list = list(chars)
    random.shuffle(chars_list)
    try:
        while len(result) < length:
            result = '{}{}'.format(
                result,
                random.choice(chars_list)
            )
    except:
        traceback.print_exc()
    return result

