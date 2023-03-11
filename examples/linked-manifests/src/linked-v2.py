import traceback
import urllib.request
from urllib.request import urlopen
import os
import shutil
import tempfile
from pathlib import Path

from py_animus.manifest_management import *
from py_animus import get_logger


class WebsiteUpTest(ManifestBase):
    """This class implements manifests of kind `WebsiteUpTest` and tests if a given URL is returning an acceptable HTTP status code
    
    Example manifest:

    ```yaml
    kind: WebsiteUpTest
    version: v1
    metadata:
      name: is-page-up
    spec:
      url: https://raw.githubusercontent.com/nicc777/py-animus/main/README.md
      acceptableResponseCodes:
      - 200
      - 201
      - 301
      - 302
    ```

    In the `spec` section, the following fields are required:

    * `spec.url` - The URL to check
    * `spec.acceptableResponseCodes` - A list if integers with acceptable HTTP response codes
    """

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache())->bool:
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
        return not variable_cache.get_value(variable_name=self.metadata['name'], value_if_expired=False, raise_exception_on_expired=False, raise_exception_on_not_found=False, default_value_if_not_found=False)

    def apply_manifest(self, manifest_lookup_function: object=None, variable_cache: VariableCache=VariableCache()):
        """Do the check if a previous check was not yet performed
        """
        self.log(message='WebsiteUpTest.apply_manifest() CALLED', level='info')
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
        return 
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):
        self.log(message='WebsiteUpTest.delete_manifest() CALLED', level='info')
        return
    

class DownloadWebPageContent(ManifestBase):
    """This class implements manifests of kind `WebsiteUpTest` and tests if a given URL is returning an acceptable HTTP status code
    
    Example manifest:

    ```yaml
    kind: DownloadWebPageContent
    version: v1
    metadata:
      name: example_page
    spec:
      url: https://raw.githubusercontent.com/nicc777/py-animus/main/README.md
      outputFile: /tmp/example-page-result/output.txt
      livenessFunction: is-page-up
    ```

    In the `spec` section, the following fields are required:

    * `spec.url` - The URL to check
    * `spec.outputFile` - The output file
    * `spec.livenessFunction` - The name of the `WebsiteUpTest` manifest that has the implementation to check if this site is alive.
    """

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v2', supported_versions: tuple=('v2',)):
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

    def _create_directory_if_not_exists(self, dir: str, variable_cache: VariableCache=VariableCache()):
        pass

    def _extract_dir_structure(self, variable_cache: VariableCache=VariableCache()):
        """
            With input like https://raw.githubusercontent.com/nicc777/py-animus/main/README.md
            Expect a dir structure `nicc777/py-animus/main` relative to `spec.outputPath`

            Input from `spec.url` (list of str)
            Result in Variable named "metadata.name:URL_SRC_DST" containing a map with the URL as key and the 
            destination directory as value

            Assumption is that the URL always points to a page and that the last part of the page represents the actual
            page, for example README.md
        """
        result = Variable(name='{}:URL_SRC_DST'.format(self.metadata['name']), logger=self.logger, initial_value=dict(), ttl=-1)
        result.value['url2destMap'] = dict()
        result.value['dst2urlMap'] = dict()
        try:
            for url in self.spec['urls']:
                dst_dir = '{}/{}'.format(
                    self.spec['outputPath'],
                    '/'.join(url.split('/')[3:-1])
                )
                dst_page = '{}/{}'.format(
                    self.spec['outputPath'],
                    '/'.join(url.split('/')[3])
                ) 
                result.value['url2destMap'][url] = dict()
                result.value['url2destMap'][url]['dst_dir'] = dst_dir
                result.value['url2destMap'][url]['dst_page'] = dst_page
                result.value['dst2urlMap'][dst_page] = url
        except:
            self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
            result.value = dict()
        variable_cache.store_variable(variable=result, overwrite_existing=True)

    def _get_current_downloaded_files(self, variable_cache: VariableCache=VariableCache()):
        """
            Walk the spec.outputPath and get all downloaded files. If they already exist, remove them from the Variable
            named "metadata.name:URL_SRC_DST"
        """
        result = Variable(name='{}:URL_SRC_DST'.format(self.metadata['name']), logger=self.logger, initial_value=dict(), ttl=-1)
        if '{}:URL_SRC_DST'.format(self.metadata['name']) in variable_cache.values:
            result = variable_cache.values['{}:URL_SRC_DST'.format(self.metadata['name'])]
        else:
            variable_cache.store_variable(variable=result, overwrite_existing=True)
            return
        try:
            for root, dirs, files in os.walk(self.spec['outputPath']):
                for file in files:
                    dst_page = '{}/{}'.format(root,file)
                    if dst_page in result.value['dst2urlMap'] is True:
                        # File already downloaded
                        url = result.value['dst2urlMap'][dst_page]
                        if url in result.value['url2destMap']:
                            # URL already downloaded - remove from `result``
                            result.value['url2destMap'].pop(url)
                            result.value['dst2urlMap'].pop(dst_page)
        except:
            self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        variable_cache.store_variable(variable=result, overwrite_existing=True)


    def _download_file(self, url: str, target_dir: str, variable_cache: VariableCache=VariableCache()):
        pass

    def apply_manifest(self, manifest_lookup_function: object=None, variable_cache: VariableCache=VariableCache()):
        self.log(message='DownloadWebPageContent.apply_manifest() CALLED', level='info')
        
        self._extract_dir_structure(variable_cache=variable_cache)
        self._get_current_downloaded_files(variable_cache=variable_cache)

        
        
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
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):
        self.log(message='DownloadWebPageContent.delete_manifest() CALLED', level='info')
        try:
            if os.path.exists(path=self.spec['outputFile']) is True:
                os.remove(path=self.spec['outputFile'])
            variable_cache.store_variable(variable=Variable(name='{}'.format(self.metadata['name']), initial_value=True, ttl=30, logger=self.logger), overwrite_existing=True)
            variable_cache.store_variable(variable=Variable(name='{}-state'.format(self.metadata['name']), initial_value='deleted', ttl=30, logger=self.logger), overwrite_existing=True)
        except:
            self.log(message='Failed to delete file {}'.format(self.spec['outputFile']), level='error')
        return 
