import traceback
import urllib.request
from urllib.request import urlopen
import os
import shutil
from pathlib import Path
from py_animus.manifest_management import *
from py_animus import get_logger


class DownloadWebPageContent(ManifestBase):
    """This class implements manifests of kind `WebsiteUpTest` and tests if a given URL is returning an acceptable HTTP status code
    
    Example manifest:

    ```yaml
    kind: DownloadWebPageContent
    version: v2
    metadata:
        name: multi_page_download
        dependencies:
            apply:
            - is-page-up
    spec:
        urls: 
        - https://raw.githubusercontent.com/nicc777/py-animus/main/README.md
        - https://raw.githubusercontent.com/nicc777/py-animus/main/doc/README.md
        outputPath: /tmp/example-page-result
        emptyOutput: true
    ```

    In the `spec` section, the following fields are required:

    * `spec.url` - The URL to check
    * `spec.outputPath` - The directory where files will be saved
    * `spec.emptyOutput` - If set to true, first empty directories and delete the directories before downloading content.
    """

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v2', supported_versions: tuple=('v2',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), target_environment: str='default')->bool:
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
        already_downloaded_qty = 0
        if 'url2destMap' in result:
            for url, file_data in result['url2destMap'].items():
                dst_file_path = str(file_data['dst_page'])
                if self._check_file_exists(file_path=dst_file_path):
                    already_downloaded_qty += 1
                    if dst_file_path in current_files:
                        current_files.remove(dst_file_path)
        if files_to_download_qty != already_downloaded_qty:
            return True
        elif len(current_files) > 0:
            return True
        return False

    def _prep_download_dir(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):
        if 'emptyOutput' in self.spec:
            if self.spec['emptyOutput'] is True:
                self.log(message='"emptyOutput" option is not implemented yet', level='warning')

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
        return current_files
    
    def _get_sub_dirs(self)->list:
        sub_dirs = list()
        for root, dirs, files in os.walk(self.spec['outputPath']):
                for dir in dirs:
                    sub_dirs.append('{}/{}'.format(root,dir))
        sub_dirs.sort(key=len, reverse=True)
        return sub_dirs

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
                    '/'.join(url.split('/')[3:])
                ) 
                Path(dst_dir).mkdir(parents=True, exist_ok=True)
                result.value['url2destMap'][url]['dst_dir'] = dst_dir
                result.value['url2destMap'][url]['dst_page'] = dst_page
                result.value['url2destMap'][url]['downloaded'] = self._check_file_exists(file_path=dst_page)
                result.value['dst2urlMap'][dst_page] = url
        except:
            self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
            result.value = dict()
        self.log(message='Variable as JSON: {}'.format(json.dumps(result.value)), level='debug')
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
            for url, file_data in result.value['url2destMap'].items():
                self.log(message='file_data={}'.format(file_data), level='debug')
                try:
                    if 'dst_page' in file_data and file_data['downloaded'] is False:
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

    def _rm_dir(self, dir: str)->bool:
        try:
            os.remove(dir)
            return True
        except:
            self.log(message='os.remove command failed. now trying shutil.rmtree', level='warning')
            try:
                shutil.rmtree(dir)
                return True
            except:
                self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        return False

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default'):
        self.log(message='DownloadWebPageContent.apply_manifest() CALLED', level='info')
        self._prep_download_dir(manifest_lookup_function=manifest_lookup_function, variable_cache=variable_cache)
        self._download_files(variable_cache=variable_cache)
        return  

    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default'):
        self.log(message='DownloadWebPageContent.delete_manifest() CALLED', level='info')
        try:
            self.log(message='Removing files', level='info')
            for file in self._get_current_downloaded_files():
                self.log(message='Removing file "{}"'.format(file), level='debug')
                os.unlink(file)
            self.log(message='Removing directories', level='info')
            for dir in self._get_sub_dirs():
                self.log(message='Removing directory "{}"'.format(dir), level='debug')
                self._rm_dir(dir=dir)
            return True
        except:
            self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
            try:
                shutil.rmtree(dir)
                return True
            except:
                self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        return False
