import traceback
import urllib.request
from urllib.request import urlopen
import copy
from py_animus.manifest_management import *
from py_animus import get_logger


class WebsiteUpTest(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache())->bool:
        """Look at the current variable_cache
        """
        return not variable_cache.get_value(variable_name=self.metadata['name'], value_if_expired=False, raise_exception_on_expired=False)

    def apply_manifest(self, manifest_lookup_function: object=None, variable_cache: VariableCache=VariableCache()):
        website_up = False
        if self.implemented_manifest_differ_from_this_manifest() is True:
            self.log(message='Testing website: {}'.format(self.spec['url']), level='info')
            try:
                return_code = urllib.request.urlopen(self.spec['url']).getcode()
                self.log(message='  return_code: {}'.format(return_code), level='info')
                if return_code in self.spec['acceptableResponseCodes']:
                    website_up = True
                else:
                    self.log(message='  Code was not found in list of acceptable return codes: {}'.format(self.spec['acceptableResponseCodes']), level='warning')
            except:
                self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
            variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=website_up, ttl=30, logger=self.logger), overwrite_existing=True)
            self.log(message='variable_cache now: {}'.format(variable_cache.values), level='debug')
        self.log(message='Is site up TEST: {}'.format(variable_cache.get_value(variable_name=self.metadata['name'])), level='debug')
        return 
    

class DownloadWebPageContent(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache())->bool:
        current_file_data = ''
        if 'outputFile' in self.spec:
            try:
                with open(self.spec['outputFile'], 'r') as f:
                    current_file_data = f.read()
                self.log(message='Data length: {}'.format(len(current_file_data)), level='info')
            except:
                self.log(message='Could not read file', level='error')
        if len(current_file_data) > 0:  # Looks like we have downloaded this before
            return False
        return True 

    def apply_manifest(self, manifest_lookup_function: object=None, variable_cache: VariableCache=VariableCache()):
        if self.implemented_manifest_differ_from_this_manifest() is False:
            self.log(message='Already retrieved {}'.format(self.spec['url']), level='info')
            return
        variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=False, ttl=30, logger=self.logger), overwrite_existing=True)
        m1 = manifest_lookup_function(name=self.spec['livenessFunction'])
        m1.apply_manifest(variable_cache=variable_cache)
        site_up = variable_cache.get_value(variable_name=self.spec['livenessFunction'], value_if_expired=False, raise_exception_on_expired=False)
        self.log(message='variable_cache now: {}'.format(variable_cache.values), level='debug')
        self.log(message='Is site up? Test={}'.format(site_up), level='info')
        if site_up is True:
            self.log(message='Retrieving {}'.format(self.spec['url']), level='info')
            try:
                content = ''
                self.log(message='Reading content from: {}'.format(self.spec['url']), level='info')
                with urlopen(self.spec['url']) as webpage:
                    content = webpage.read().decode()
                with open(self.spec['outputFile'], 'w') as of:
                    of.write(content)
                self.log(message='Saved content in {}'.format(self.spec['outputFile']), level='info')
                variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=True, ttl=30, logger=self.logger), overwrite_existing=True)
            except:
                self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        return  
