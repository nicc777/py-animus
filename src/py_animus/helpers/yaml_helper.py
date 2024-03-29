"""
    Taken verbatim from https://gist.github.com/lukeplausin/0f103517d718ce6844180b4ccf212775 on 2023-07-22 with the exception of the load_from_str() function

    Credit goes to https://gist.github.com/lukeplausin
"""

import yaml
import traceback
import copy
import re
from py_animus.models import VariableCache, AllScopedValues, all_scoped_values, variable_cache, scope
from py_animus.models.extensions import ManifestBase
from py_animus.animus_logging import logger
from py_animus.extensions import extensions

try:    # pragma: no cover
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError: # pragma: no cover
    from yaml import Loader, Dumper


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


# class SafeUnknownRepresenter(yaml.representer.SafeRepresenter):
#     def represent_data(self, wrapdata):
#         tag = False
#         if type(wrapdata).__name__.startswith('TagWrap_'):
#             datatype = getattr(wrapdata, "wrapType")
#             tag = getattr(wrapdata, "wrapTag")
#             data = datatype(wrapdata)
#         else:
#             data = wrapdata
#         node = super(SafeUnknownRepresenter, self).represent_data(data)
#         if tag:
#             node.tag = tag
#         return node

# class SafeUnknownDumper(SafeUnknownRepresenter, yaml.dumper.SafeDumper):

#     def __init__(self, stream,
#             default_style=None, default_flow_style=False,
#             canonical=None, indent=None, width=None,
#             allow_unicode=None, line_break=None,
#             encoding=None, explicit_start=None, explicit_end=None,
#             version=None, tags=None, sort_keys=True):

#         SafeUnknownRepresenter.__init__(self, default_style=default_style,
#                 default_flow_style=default_flow_style, sort_keys=sort_keys)

#         yaml.dumper.SafeDumper.__init__(self,  stream,
#                                         default_style=default_style,
#                                         default_flow_style=default_flow_style,
#                                         canonical=canonical,
#                                         indent=indent,
#                                         width=width,
#                                         allow_unicode=allow_unicode,
#                                         line_break=line_break,
#                                         encoding=encoding,
#                                         explicit_start=explicit_start,
#                                         explicit_end=explicit_end,
#                                         version=version,
#                                         tags=tags,
#                                         sort_keys=sort_keys)


# def load_handle(f):
#     MySafeLoader = SafeUnknownLoader
#     yaml.constructor.SafeConstructor.add_constructor(None, SafeUnknownConstructor.construct_undefined)
#     return yaml.load(f, MySafeLoader)


def load_from_str_and_ignore_custom_tags(s: str)->dict:
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


def spit_yaml_text_from_file_with_multiple_yaml_sections(yaml_text: str)->dict:
    yaml_sections = dict()  # index is the "kind" each section, with the value a list of manifests of that kind
    section_text = ''
    with open(yaml_text, 'r') as f:
        for line in f:
            if line.startswith('---'):  # YAML Section start
                yaml_sections = add_new_yaml_section_to_yaml_sections(yaml_sections=copy.deepcopy(yaml_sections), section_text=section_text)
                section_text = ''
            else:
                line = line.replace('\n', '')
                line = line.replace('\r', '')
                if len(section_text) > 0:    
                    section_text = '{}\n{}'.format(section_text, line)
                else:
                    section_text = '{}'.format(line)
    if len(section_text) > 0:
        yaml_sections = add_new_yaml_section_to_yaml_sections(yaml_sections=copy.deepcopy(yaml_sections), section_text=section_text)
    return yaml_sections


#######################################################################################################################
###                                                                                                                 ###
###                                 I M P O R T    W I T H    C U S T O M    T A G S                                ###
###                                                                                                                 ###
#######################################################################################################################


class ValuePlaceholder:

    def __init__(self, placeholder_name: str):
        self.placeholder_name = placeholder_name
        self.per_environment_values = dict()

    def add_environment_value(self, value: object):
        if value is not None:
            if isinstance(value, str):
                value = value.replace('\n', '')
                value = value.replace('\r', '')
        self.per_environment_values[scope.value] = value

    def get_environment_value(self, default_value_when_not_found: object=None, raise_exception_when_not_found: bool=True):
        if scope.value not in self.per_environment_values:
            if raise_exception_when_not_found is True:
                raise Exception('No value for environment "{}" for value placeholder "{}" found'.format(scope.value, self.placeholder_name))
            return default_value_when_not_found
        return copy.deepcopy(self.per_environment_values[scope.value])
    
    def to_dict(self):
        data = dict()
        data['name'] = self.placeholder_name
        data['environments'] = list()
        for env_name, env_val in self.per_environment_values.items():
            pev = dict()
            pev['environmentName'] = env_name
            pev['value'] = env_val
            data['environments'].append(copy.deepcopy(pev))
        return data


class ValuePlaceHolders:

    def __init__(self):
        self.value_placeholder_names = dict()

    def value_placeholder_exists(self, placeholder_name: str)->bool:
        if placeholder_name in self.value_placeholder_names:
            return True
        return False

    def get_value_placeholder(self, placeholder_name: str, create_in_not_exists: bool=True)->ValuePlaceholder:
        if self.value_placeholder_exists(placeholder_name=placeholder_name) is False and create_in_not_exists is True:
            return self.create_new_value_placeholder(placeholder_name=placeholder_name)
        elif self.value_placeholder_exists(placeholder_name=placeholder_name) is False and create_in_not_exists is False:
            raise Exception('ValuePlaceholder named "{}" not found'.format(placeholder_name))
        return copy.deepcopy(self.value_placeholder_names[placeholder_name])

    def create_new_value_placeholder(self, placeholder_name: str)->ValuePlaceholder:
        vp = ValuePlaceholder(placeholder_name=placeholder_name)
        self.value_placeholder_names[placeholder_name] = copy.deepcopy(vp)
        return copy.deepcopy(vp)
    
    def add_environment_value(self, placeholder_name: str, value: object):
        if isinstance(value, str) is False:
            try:
                value = str(value)
            except:
                logger.error('Failed to get resolved value for placeholder_name "{}"'.format(placeholder_name))
        vp = self.get_value_placeholder(placeholder_name=placeholder_name, create_in_not_exists=True)
        vp.add_environment_value(value=value)
        self.value_placeholder_names[placeholder_name] = copy.deepcopy(vp)

    def to_dict(self):
        data = dict()
        data['values'] = list()
        for vp_name in list(self.value_placeholder_names.keys()):
            vp = self.get_value_placeholder(placeholder_name=vp_name)
            data['values'].append(vp.to_dict())
        return data

    def parse_and_replace_placeholders_in_string(
            self,
            input_str: str,
            default_value_when_not_found: object='',
            raise_exception_when_not_found: bool=False
        ):
        logger.debug('Parsing for placeholders. input_str="{}"'.format(input_str))
        return_str = copy.deepcopy(input_str)
        if input_str.find('{}{}'.format('$', '{')) >= 0:
            for matched_placeholder in re.findall('\$\{([\w|\s|\-|\_|\.|\:]+)\}', input_str):
                val = self.get_value_placeholder(
                    placeholder_name=matched_placeholder,
                    create_in_not_exists=True
                ).get_environment_value(
                    default_value_when_not_found=default_value_when_not_found,
                    raise_exception_when_not_found=raise_exception_when_not_found
                )
                logger.debug('(pre) val type={}'.format(type(val)))
                if val is None:
                    val = ''
                    logger.warning('NoneType detected')
                if isinstance(val, str) is False:
                    val = '{}'.format(str(val))
                logger.debug('val={}   type={}'.format(val, type(val)))
                return_str = return_str.replace('{}{}{}{}'.format('$', '{', matched_placeholder, '}'),val)
        logger.debug('   return_str="{}'.format(return_str))
        return return_str


class ValueTag(yaml.YAMLObject):
    yaml_tag = u'!Value'

    def __init__(self, value_reference):
        self.value_reference = value_reference
        self.resolved_value = copy.deepcopy(all_scoped_values.find_scoped_values(scope=scope.value).find_value_by_name(name=self.value_reference))

    def __repr__(self):
        return self.resolved_value.value
    
    def __str__(self):
        if self.resolved_value.value is None:
            return ''
        return self.resolved_value.value
    
    @classmethod
    def from_yaml(cls, loader, node):
        return ValueTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value_reference)


class VariableTag(yaml.YAMLObject):
    yaml_tag = u'!Variable'

    def __init__(self, variable_reference):
        self.variable_reference = variable_reference
        self.resolved_value = copy.deepcopy(
            variable_cache.get_value(
                variable_name='{}'.format(copy.deepcopy(variable_reference)),
                value_if_expired=None,
                raise_exception_on_expired=True,
                raise_exception_on_not_found=True,
                default_value_if_not_found=None,
                init_with_default_value_if_not_found=False,
                for_logging=False
            )
        )
        if isinstance(self.resolved_value, str):
            self.resolved_value = "{}".format(self.resolved_value)

    def __repr__(self):
        return self.resolved_value
    
    def __str__(self):
        return self.resolved_value

    @classmethod
    def from_yaml(cls, loader, node):
        return VariableTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.variable_reference)


def parse_sub_yaml(raw_yaml_str: str)->dict:
    logger.debug('Parsing input YAML: {}'.format(raw_yaml_str))
    yaml.SafeLoader.add_constructor(        '!Value',       ValueTag.from_yaml      )
    yaml.SafeLoader.add_constructor(        '!Variable',    VariableTag.from_yaml   )
    yaml.SafeDumper.add_multi_representer(  ValueTag,       ValueTag.to_yaml        )
    yaml.SafeDumper.add_multi_representer(  VariableTag,    VariableTag.to_yaml     )
    manifest_data = yaml.safe_load(raw_yaml_str)
    # converted_data = dict((k.lower(),v) for k,v in manifest_data.items()) # Convert keys to lowercase
    return manifest_data


class SubTag(yaml.YAMLObject):
    yaml_tag = u'!Sub'

    def __init__(self, value_reference):
        if isinstance(value_reference, list) is False:
            raise Exception('!Sub tag only accepts lists at this time. The first item is a string and subsequent list items are key/value pairs of variables to replace in the string.')
        value_placeholders = ValuePlaceHolders()
        self.value_reference = value_reference

        main_line = ''
        for sub_node in value_reference:
            if isinstance(sub_node, yaml.ScalarNode):
                main_line = sub_node.value
            elif isinstance(sub_node, yaml.MappingNode):
                for key_value_pair in sub_node.value:
                    yaml_key = key_value_pair[0].value
                    key_tag = key_value_pair[0].tag
                    yaml_value = key_value_pair[1].value
                    value_tag = key_value_pair[1].tag
                    if '!Variable' in value_tag:
                        yaml_value = '!Variable {}'.format(yaml_value)
                    elif '!Value' in value_tag:
                        yaml_value = '!Value {}'.format(yaml_value)

                    # TODO build interim YAML and call parse_animus_formatted_yaml() again...
                    
                    parsed_tag_data = parse_sub_yaml(raw_yaml_str='{}: {}'.format(yaml_key, yaml_value))
                    parsed_value = parsed_tag_data[yaml_key]

                    # if isinstance(parsed_value, str) and parsed_value.startswith('!V') is False:
                    #     parsed_value = "'{}'".format(parsed_value)

                    value_placeholders.create_new_value_placeholder(placeholder_name=yaml_key)
                    value_placeholders.add_environment_value(placeholder_name=yaml_key, value=parsed_value)
        # self.resolved_value = value_placeholders.parse_and_replace_placeholders_in_string(input_str=main_line, default_value_when_not_found=None, raise_exception_when_not_found=True)
        self.resolved_value = value_placeholders.parse_and_replace_placeholders_in_string(input_str=main_line, default_value_when_not_found='', raise_exception_when_not_found=False)
        logger.debug('resolved_value={}'.format(self.resolved_value))
        

    def __repr__(self):
        return self.resolved_value
    
    def __str__(self):
        return self.resolved_value
    
    @classmethod
    def from_yaml(cls, loader, node):
        return SubTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value_reference)


def parse_animus_formatted_yaml(raw_yaml_str: str)->ManifestBase:
    IGNORED_KINDS = (
        'Values',   # These manifests should by now already be parsed...
    )

    logger.debug('Parsing input YAML: {}'.format(raw_yaml_str))

    yaml.SafeLoader.add_constructor(        '!Value',       ValueTag.from_yaml      )
    yaml.SafeLoader.add_constructor(        '!Variable',    VariableTag.from_yaml   )
    yaml.SafeLoader.add_constructor(        '!Sub',         SubTag.from_yaml        )
    
    yaml.SafeDumper.add_multi_representer(  ValueTag,       ValueTag.to_yaml        )
    yaml.SafeDumper.add_multi_representer(  VariableTag,    VariableTag.to_yaml     )
    yaml.SafeDumper.add_multi_representer(  SubTag,         SubTag.to_yaml          )
    
    manifest_data = yaml.safe_load(raw_yaml_str)
    converted_data = dict((k.lower(),v) for k,v in manifest_data.items()) # Convert keys to lowercase
    if 'kind' in converted_data and 'version' in converted_data:
        if converted_data['kind'] not in IGNORED_KINDS:
            manifest_class = extensions.find_extension_that_supports_version(extension_kind=converted_data['kind'], version=converted_data['version'])
            initialized_manifest_class = manifest_class()
            initialized_manifest_class.parse_manifest(manifest_data=manifest_data)
            return initialized_manifest_class
    else:
        raise Exception('Expected key "Kind" and "Version". One or both of these keys are missing')


def parse_raw_yaml_data_and_ignore_all_tags(yaml_data: str, use_custom_parser_for_custom_tags: bool=False)->dict:
    if use_custom_parser_for_custom_tags is True:
        return load_from_str_and_ignore_custom_tags(s=yaml_data)
    configuration = dict()
    current_part = 0
    try:
        for data in yaml.load_all(yaml_data, Loader=Loader):
            current_part += 1
            configuration['part_{}'.format(current_part)] = data
    except: # pragma: no cover
        try:
            # Even though the use_custom_parser_for_custom_tags flag was False, let's try using the custom parser
            parsed_data = load_from_str_and_ignore_custom_tags(s=yaml_data)
            logger.warning('It seems the YAML contained custom tags !!! WARNING: This conversion only works ONE WAY. You will not be able to reconstruct the original YAML from the resulting dict')
            return parsed_data
        except:
            traceback.print_exc()
            raise Exception('Failed to parse configuration')
    return configuration