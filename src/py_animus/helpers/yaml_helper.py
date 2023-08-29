"""
    Taken verbatim from https://gist.github.com/lukeplausin/0f103517d718ce6844180b4ccf212775 on 2023-07-22 with the exception of the load_from_str() function

    Credit goes to https://gist.github.com/lukeplausin
"""

import yaml
import traceback
import copy
from py_animus.models import VariableCache, AllScopedValues, all_scoped_values, variable_cache, scope


#######################################################################################################################
###                                                                                                                 ###
###               I M P O R T    A N D    C O M P L E T E L Y    I G N O R E    C U S T O M    T A G S              ###
###                                                                                                                 ###
#######################################################################################################################


class SafeUnknownConstructor(yaml.constructor.SafeConstructor):
    def __init__(self):
        yaml.constructor.SafeConstructor.__init__(self)

    def construct_undefined(self, node):
        data = getattr(self, 'construct_' + node.id)(node)
        datatype = type(data)
        wraptype = type('TagWrap_'+datatype.__name__, (datatype,), {})
        wrapdata = wraptype(data)
        wrapdata.tag = lambda: None
        wrapdata.datatype = lambda: None
        setattr(wrapdata, "wrapTag", node.tag)
        setattr(wrapdata, "wrapType", datatype)
        return wrapdata


class SafeUnknownLoader(SafeUnknownConstructor, yaml.loader.SafeLoader):

    def __init__(self, stream):
        SafeUnknownConstructor.__init__(self)
        yaml.loader.SafeLoader.__init__(self, stream)


class SafeUnknownRepresenter(yaml.representer.SafeRepresenter):
    def represent_data(self, wrapdata):
        tag = False
        if type(wrapdata).__name__.startswith('TagWrap_'):
            datatype = getattr(wrapdata, "wrapType")
            tag = getattr(wrapdata, "wrapTag")
            data = datatype(wrapdata)
        else:
            data = wrapdata
        node = super(SafeUnknownRepresenter, self).represent_data(data)
        if tag:
            node.tag = tag
        return node

class SafeUnknownDumper(SafeUnknownRepresenter, yaml.dumper.SafeDumper):

    def __init__(self, stream,
            default_style=None, default_flow_style=False,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None, sort_keys=True):

        SafeUnknownRepresenter.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style, sort_keys=sort_keys)

        yaml.dumper.SafeDumper.__init__(self,  stream,
                                        default_style=default_style,
                                        default_flow_style=default_flow_style,
                                        canonical=canonical,
                                        indent=indent,
                                        width=width,
                                        allow_unicode=allow_unicode,
                                        line_break=line_break,
                                        encoding=encoding,
                                        explicit_start=explicit_start,
                                        explicit_end=explicit_end,
                                        version=version,
                                        tags=tags,
                                        sort_keys=sort_keys)


def load_handle(f):
    MySafeLoader = SafeUnknownLoader
    yaml.constructor.SafeConstructor.add_constructor(None, SafeUnknownConstructor.construct_undefined)
    return yaml.load(f, MySafeLoader)


def load_from_str(s: str)->dict:
    MySafeLoader = SafeUnknownLoader
    yaml.constructor.SafeConstructor.add_constructor(None, SafeUnknownConstructor.construct_undefined)
    configuration = dict()
    current_part = 0
    try:
        for data in yaml.load_all(s, Loader=MySafeLoader):
            current_part += 1
            configuration['part_{}'.format(current_part)] = data
    except: # pragma: no cover
        traceback.print_exc()
        raise Exception('Failed to parse configuration')
    return configuration


#######################################################################################################################
###                                                                                                                 ###
###                                     Y A M L    F I L E    F U N C T I O N S                                     ###
###                                                                                                                 ###
#######################################################################################################################


def get_kind_from_text(text: str):
    for line in text.splitlines():
        if line.lower().startswith('kind:'):
            kind = line.split(':')[1].strip()
            return kind
    return 'unknown'


def add_new_yaml_section_to_yaml_sections(yaml_sections: dict, section_text: str)->dict:
    if len(section_text) > 0:
        kind = get_kind_from_text(text = section_text)
        if kind not in yaml_sections:
            yaml_sections[kind] = list()
        yaml_sections[kind].append(section_text)
    return copy.deepcopy(yaml_sections)


def spit_yaml_file_with_multiple_yaml_sections(yaml_file: str)->dict:
    yaml_sections = dict()  # index is the "kind" each section, with the value a list of manifests of that kind
    section_text = ''
    with open(yaml_file, 'r') as f:
        for line in f:
            if line.startswith('---'):  # YAML Section start
                yaml_sections = add_new_yaml_section_to_yaml_sections(yaml_sections=copy.deepcopy(yaml_sections), section_text=section_text)
                section_text = ''
            else:
                if len(section_text) > 0:
                    section_text = '{}\n{}'.format(section_text, line.strip())
                else:
                    section_text = '{}'.format(line.strip())
    if len(section_text) > 0:
        yaml_sections = add_new_yaml_section_to_yaml_sections(yaml_sections=copy.deepcopy(yaml_sections), section_text=section_text)
    return yaml_sections


#######################################################################################################################
###                                                                                                                 ###
###                                 I M P O R T    W I T H    C U S T O M    T A G S                                ###
###                                                                                                                 ###
#######################################################################################################################


class ValueTag(yaml.YAMLObject):
    yaml_tag = u'!Value'

    def __init__(self, value_reference):
        self.value_reference = value_reference

    def __repr__(self):
        return all_scoped_values.find_scoped_values(scope=scope).find_value_by_name(name=self.value_reference)

    @classmethod
    def from_yaml(cls, loader, node):
        return ValueTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.txt_var_original)


