import traceback
import urllib.request
from urllib.request import urlopen
import os
import shutil
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

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v2', supported_versions: tuple=('v1', 'v2',)):
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
        self._extract_dir_structure(variable_cache=variable_cache)
        result = variable_cache.get_value(
            variable_name='{}:URL_SRC_DST'.format(self.metadata['name']),
            value_if_expired=dict(),
            default_value_if_not_found=dict(),
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        )
        files_to_download_qty = len(self.spec['urls'])
        current_files = self._get_current_downloaded_files()
        already_downloaded = 0
        if 'url2destMap' in result:
            for url, file_data in result['url2destMap'].items():
                dst_file_path = str(file_data['dst_page'])
                if self._check_file_exists(file_path=dst_file_path):
                    already_downloaded += 1
                    if dst_file_path in current_files:
                        current_files.pop(dst_file_path)
        if files_to_download_qty != len(already_downloaded):
            return True
        elif len(current_files) > 0:
            return True
        return False

    def _get_current_downloaded_files(self)->list:
        """
            Walk the spec.outputPath and get all downloaded files. If they already exist, remove them from the Variable
            named "metadata.name:URL_SRC_DST"
        """
        current_files = list()
        try:
            for root, dirs, files in os.walk(self.spec['outputPath']):
                for file in files:
                    current_files.append('{}/{}'.format(root,file))
        except:
            self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        return current_files()

    def _check_file_exists(self, file_path: str)->bool:
        if os.path.exists(file_path):
            if os.path.isfile(file_path) is True:
                return True
        return False

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
                result.value['url2destMap'][url] = dict()
                dst_dir = '{}/{}'.format(
                    self.spec['outputPath'],
                    '/'.join(url.split('/')[3:-1])
                )
                dst_page = '{}/{}'.format(
                    self.spec['outputPath'],
                    '/'.join(url.split('/')[3])
                ) 
                Path(dst_dir).mkdir(parents=True, exist_ok=True)
                result.value['url2destMap'][url]['dst_dir'] = dst_dir
                result.value['url2destMap'][url]['dst_page'] = dst_page
                result.value['url2destMap'][url]['downloaded'] = self._check_file_exists(file_path=dst_page)
                result.value['dst2urlMap'][dst_page] = url
        except:
            self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
            result.value = dict()
        variable_cache.store_variable(variable=result, overwrite_existing=True)

    def _get_current_result_variable_instance(self, variable_cache: VariableCache=VariableCache())->Variable:
        result = Variable(name='{}:URL_SRC_DST'.format(self.metadata['name']), logger=self.logger, initial_value=dict(), ttl=-1)
        if '{}:URL_SRC_DST'.format(self.metadata['name']) in variable_cache.values:
            result = copy.deepcopy(variable_cache.values['{}:URL_SRC_DST'.format(self.metadata['name'])])
        else:
            variable_cache.store_variable(variable=result, overwrite_existing=True)
        return result

    def _download_files(self, variable_cache: VariableCache=VariableCache()):
        result = self._get_current_result_variable_instance(variable_cache=variable_cache)
        if 'url2destMap' in result.value:
            for url, file_data in result['url2destMap'].items():
                try:
                    if 'dst_page' in file_data and result.value['url2destMap'][url]['downloaded'] is False:
                        content = ''
                        self.log(message='Reading content from: {}'.format(url), level='info')
                        with urlopen(url) as webpage:
                            content = webpage.read().decode()
                        with open(file_data['dst_page'], 'w') as of:
                            of.write(content)
                        self.log(message='Saved content in {}'.format(file_data['dst_page']), level='info')
                        result.value['url2destMap'][url]['downloaded'] = True
                except:
                    self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        variable_cache.store_variable(variable=result, overwrite_existing=True)

    def apply_manifest(self, manifest_lookup_function: object=None, variable_cache: VariableCache=VariableCache()):
        self.log(message='DownloadWebPageContent.apply_manifest() CALLED', level='info')
        self._download_files(variable_cache=variable_cache)
        return  
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):
        self.log(message='DownloadWebPageContent.delete_manifest() CALLED', level='info')
        try:
            os.remove(dir)
            return True
        except:
            self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
            try:
                shutil.rmtree(dir)
                return True
            except:
                self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        return False
