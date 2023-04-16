import traceback
import urllib.request
from urllib.request import urlopen
import os
from py_animus.manifest_management import *
from py_animus import get_logger


class WebsiteUpTest(ManifestBase):
    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
        self.execution_count = 0

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), target_environment: str='default')->bool:
        """Look at the current variable_cache to determine if a check was already made recently

        It will look in the `variable_cache` for a variable named `is-page-up`.

        Decision table:

        | Variable Exists | Final Variable Value | Change Detected |
        |:---------------:|:--------------------:|:---------------:|
        | No              | False                | True            |
        | Yes             | False                | True            |
        | Yes (Expired)   | False                | True            |
        | Yes             | True (Stored value)  | False           |
        """
        already_checked = not variable_cache.get_value(variable_name=self.metadata['name'], value_if_expired=False, raise_exception_on_expired=False, raise_exception_on_not_found=False, default_value_if_not_found=False)
        self.log(message='already_checked={}'.format(already_checked), level='info')
        return already_checked

    def _record_execution_count(self)->int:
        self.execution_count += 1
        return self.execution_count

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default'):
        """Do the check if a previous check was not yet performed
        """
        self.log(message='WebsiteUpTest.apply_manifest() CALLED', level='info')
        
        if self._record_execution_count() > 1 and 'executeOnlyOnceOnApply' in self.metadata:
            if self.metadata['executeOnlyOnceOnApply'] is True:
                self.log(message='executeOnlyOnceOnApply set to True and previous execution detected: {}'.format(self.spec['url']), level='info')
                return
        
        if variable_cache.get_value(variable_name=self.metadata['name'], value_if_expired=False, raise_exception_on_expired=False, raise_exception_on_not_found=False, default_value_if_not_found=False) is False:
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
                self.log(message='variable_cache now: {}'.format(str(variable_cache)), level='debug')
            variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=website_up, ttl=30, logger=self.logger), overwrite_existing=True)
            self.log(message='Is site up TEST: {}'.format(variable_cache.get_value(variable_name=self.metadata['name'])), level='debug')
        else:
            self.log(message='Already checked', level='info')
        return 
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default'):
        self.log(message='WebsiteUpTest.delete_manifest() CALLED', level='info')
        if self._record_execution_count() > 1 and 'executeOnlyOnceOnDelete' in self.metadata:
            if self.metadata['executeOnlyOnceOnDelete'] is True:
                self.log(message='executeOnlyOnceOnDelete set to True and previous execution detected: {}'.format(self.spec['url']), level='info')
                return
        return
    

class DownloadWebPageContent(ManifestBase):
    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache())->bool:
        """Attempt to see if the page was previously downloaded with the following checks:

        1) First check if there was somehow a delete action before this apply action by checking for the variable named '{}-state'.format(self.metadata['name'])
        2) Try to read the downloaded file. If the file can be read and has more than 0 bytes, assume it was already downloaded
        """
        previously_delete = variable_cache.get_value(variable_name='{}-state'.format(self.metadata['name']), value_if_expired='unknown', raise_exception_on_expired=False, raise_exception_on_not_found=False, default_value_if_not_found='unknown')
        if previously_delete == 'applied':
            self.log(message='Appears to have recently been applied - no further action required. Returning no differences found status', level='warning')
            return False    # Must have been recently applied
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

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False):
        """The apply process works implements the following flow:

        1) Check if the file has previously been downloaded - if so, no further processing is required and the method returns
        2) Check if the remote site is up by calling to the `WebsiteUpTest` manifest implementations apply action. If the site is not up, return
        3) Download the page content
        4) Save to a file defined in the Manifest
        5) Set variables and return
        """
        self.log(message='DownloadWebPageContent.apply_manifest() CALLED', level='info')
        if self.implemented_manifest_differ_from_this_manifest() is False:
            self.log(message='Already retrieved {}'.format(self.spec['url']), level='info')
            variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=True, ttl=30, logger=self.logger), overwrite_existing=True)
            variable_cache.store_variable(variable=Variable(name='{}-state'.format(self.metadata['name']), initial_value='applied', ttl=30, logger=self.logger), overwrite_existing=True)
            return
        variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=False, ttl=30, logger=self.logger), overwrite_existing=True)
        site_up = variable_cache.get_value(variable_name=self.metadata['dependencies']['apply'][0], value_if_expired=False, raise_exception_on_expired=False)
        self.log(message='variable_cache now: {}'.format(str(variable_cache)), level='debug')
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
                variable_cache.store_variable(variable=Variable(name='{}-state'.format(self.metadata['name']), initial_value='applied', ttl=30, logger=self.logger), overwrite_existing=True)
            except:
                self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
                variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=False, ttl=30, logger=self.logger), overwrite_existing=True)
                variable_cache.store_variable(variable=Variable(name='{}-state'.format(self.metadata['name']), initial_value='not-applied', ttl=30, logger=self.logger), overwrite_existing=True)
        return  
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False):
        self.log(message='DownloadWebPageContent.delete_manifest() CALLED', level='info')
        try:
            if os.path.exists(path=self.spec['outputFile']) is True:
                os.remove(path=self.spec['outputFile'])
            variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=True, ttl=30, logger=self.logger), overwrite_existing=True)
            variable_cache.store_variable(variable=Variable(name='{}-state'.format(self.metadata['name']), initial_value='deleted', ttl=30, logger=self.logger), overwrite_existing=True)
        except:
            self.log(message='Failed to delete file {}'.format(self.spec['outputFile']), level='error')
        return 
