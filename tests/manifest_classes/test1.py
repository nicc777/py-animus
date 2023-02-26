from py_animus.manifest_management import *
from py_animus import get_logger, parse_yaml_file


def my_post_parsing_method(**params):
    print('Working with parameters: {}'.format(params))
    return


class MyManifest1(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v0.1', supported_versions: tuple=('v0.1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function)->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
        return  # Assume some implementation