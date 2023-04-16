from py_animus.manifest_management import *
from py_animus import get_logger, parse_raw_yaml_data


def my_post_parsing_method(**params):
    print('Working with parameters: {}'.format(params))
    return


class MyManifest1(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v0.2', supported_versions: tuple=('v0.1', 'v0.2',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), target_environment: str='default')->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default'):
        variable_cache.store_variable(
            variable=Variable(
                name='{}:{}'.format(
                    self.kind, self.metadata['name']
                ), 
                initial_value='Result from MyManifest1 "{}" applying manifest named "{}" with manifest version "{}"'.format(
                    self.version,
                    self.metadata['name'],
                    self.ingested_manifest_version
                )
            )
        )
        self.log(
            message='Applied implementation kind "{}" of version "{}" with manifest checksum "{}"'.format(
                self.metadata['name'],
                self.version,
                self.checksum
            ),
            level='info'
        )
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=self.spec['val']), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=True)
        return  # Assume some implementation
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default'):
        try:
            var = variable_cache.values['{}:{}'.format(self.kind, self.metadata['name'])]
            if var is not None:
                var.ttl = 1
                var.init_timestamp = 1
            variable_cache.store_variable(variable=var, overwrite_existing=True) # Store the expired version of this deleted variable
        except:
            self.log(message='Looks like "{}" version "{}" was deleted already'.format(self.metadata['name'],self.version,), level='warning')
        self.log(
            message='Deleted implementation kind "{}" of version "{}" with manifest checksum "{}"'.format(
                self.metadata['name'],
                self.version,
                self.checksum
            ),
            level='info'
        )
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=None), overwrite_existing=False)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=False)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        return