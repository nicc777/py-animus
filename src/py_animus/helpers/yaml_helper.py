"""
    Taken verbatim from https://gist.github.com/lukeplausin/0f103517d718ce6844180b4ccf212775 on 2023-07-22 with the exception of the load_from_str() function

    Credit goes to https://gist.github.com/lukeplausin
"""

import yaml
import traceback


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
    # logger.debug('parse_raw_yaml_data(): RAW DATA: {}'.format(yaml_data))
    try:
        for data in yaml.load_all(s, Loader=MySafeLoader):
            current_part += 1
            configuration['part_{}'.format(current_part)] = data
        # logger.debug('configuration={}'.format(configuration))
    except: # pragma: no cover
        traceback.print_exc()
        raise Exception('Failed to parse configuration')
    return configuration
