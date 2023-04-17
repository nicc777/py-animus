from py_animus.manifest_management import *
from py_animus import get_logger
import traceback


class HelloWorld(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders())->bool:
        current_file_data = None
        if 'file' in self.spec:
            try:
                with open(self.spec['file'], 'r') as f:
                    current_file_data = f.read()
            except:
                self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        if 'content' in self.spec:
            if self.spec['content'] == current_file_data:
                return False
        return True 

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        if self.implemented_manifest_differ_from_this_manifest() is True:
            self.log(message='Not yet applied. Applying "{}" named "{}"'.format(self.kind, self.metadata['name']), level='info')
            if 'file' in self.spec and 'content' in self.spec:
                try:
                    with open(self.spec['file'], 'w') as f:
                        f.write(self.spec['content'])
                except:
                    self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        else:
            self.log(message='Already Applied "{}" named "{}"'.format(self.kind, self.metadata['name']), level='info')
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value=True, logger=self.logger), overwrite_existing=True)
        return 
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        try:
            if os.path.exists(path=self.spec['file']) is True:
                os.remove(path=self.spec['file'])
            variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value=False, logger=self.logger), overwrite_existing=True)
            variable_cache.store_variable(variable=Variable(name='{}-state'.format(self.metadata['name']), initial_value='deleted', ttl=30, logger=self.logger), overwrite_existing=True)
        except:
            self.log(message='Failed to delete file {}'.format(self.spec['outputFile']), level='error')
        return 
