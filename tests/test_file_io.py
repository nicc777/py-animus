"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.manifest_management import *
from py_animus.utils import *
from py_animus.file_io import *

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))

class TestFileIoCreateDirs(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_create_temp_dir(self):
        tmp_dir = create_temp_directory()
        print('test_create_temp_dir(): tmp_dir={}'.format(tmp_dir))
        self.assertIsNotNone(tmp_dir)
        self.assertIsInstance(tmp_dir, str)
        self.assertTrue(os.path.isdir(tmp_dir))
        delete_directory(dir=tmp_dir)
        self.assertFalse(os.path.exists(tmp_dir))

    def test_create_temp_dir_with_sub_dir(self):
        tmp_dir = create_temp_directory()
        sub_dir = '{}{}test1'.format(tmp_dir, os.sep)
        create_directory(path=sub_dir)
        print('test_create_temp_dir(): tmp_dir={}'.format(tmp_dir))
        self.assertIsNotNone(sub_dir)
        self.assertIsInstance(sub_dir, str)
        self.assertTrue(os.path.isdir(sub_dir))
        delete_directory(dir=tmp_dir)
        self.assertFalse(os.path.exists(tmp_dir))


def dir_list_callback_strips_metadata(current_root: str, current_result: dict)->dict:   # pragma: no cover
    new_result = dict()
    for file_with_full_path, file_meta_data in current_result.items():
        new_result[file_with_full_path] = dict()
    return new_result


class TestFileIoListingFunctions(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        print()
        self.tmp_dir = create_temp_directory()
        self.dir_setup_data = (
            {
                'dir': '{}{}dir1'.format(self.tmp_dir, os.sep),
                'files': [
                    {
                        'file1.txt': 'content {}'.format(generate_random_string(length=8)) # Total length = 8+8 = 16
                    },
                    {
                        'file2.txt': 'content {}'.format(generate_random_string(length=16)) # Total length = 8+16 = 24
                    },
                ],
            },
            {
                'dir': '{}{}dir2'.format(self.tmp_dir, os.sep),
                'files': [
                    {
                        'file3.txt': 'content {}'.format(generate_random_string(length=16)) 
                    },
                    {
                        'file4.txt': 'content {}'.format(generate_random_string(length=32)) 
                    },
                ],
            },
            {
                'dir': '{}{}dir1{}subdir1'.format(self.tmp_dir, os.sep, os.sep),
                'files': [
                    {
                        'file5.txt': 'content {}'.format(generate_random_string(length=12)) 
                    },
                    {
                        'file6.txt': 'content {}'.format(generate_random_string(length=22)) 
                    },
                    {
                        'file7.txt': 'content {}'.format(generate_random_string(length=32)) 
                    },
                    {
                        'file8.txt': 'content {}'.format(generate_random_string(length=42)) 
                    },
                ],
            },
            {
                'dir': '{}{}dir1{}subdir2'.format(self.tmp_dir, os.sep, os.sep),
                'files': [
                    {
                        'file9.txt': 'content {}'.format(generate_random_string(length=52)) 
                    },
                    {
                        'file10.txt': 'content {}'.format(generate_random_string(length=62)) 
                    },
                ],
            },
            {
                'dir': '{}{}dir2{}subdir3'.format(self.tmp_dir, os.sep, os.sep),
                'files': [],
            },
            {
                'dir': '{}{}dir2{}subdir3{}subdir4'.format(self.tmp_dir, os.sep, os.sep, os.sep),
                'files': [
                    {
                        'file11.txt': 'content {}'.format(generate_random_string(length=72)) 
                    },
                    {
                        'file12.txt': 'content {}'.format(generate_random_string(length=82)) 
                    },
                    {
                        'file13.txt': 'content {}'.format(generate_random_string(length=92)) 
                    },
                ],
            },
        )
        print('PREPARING DIRECTORIES AND FILES')
        for test_data in self.dir_setup_data:
            dir_name = test_data['dir']
            create_directory(path=dir_name)
            print('* Created directory "{}"'.format(dir_name))
            for test_file_data in test_data['files']:
                for file_name, file_content in test_file_data.items():
                    with open('{}{}{}'.format(dir_name, os.sep, file_name), 'w') as f:
                        f.write(file_content)
                    print('   - Created file "{}"'.format(file_name))
        print('SETUP COMPLETE')
        print()
        
    def tearDown(self):
        print()
        print()
        print('DELETING DIRECTORIES')
        delete_directory(dir=self.tmp_dir)
        print('* Deleted directory "{}"'.format(self.tmp_dir))
        print()
        print()

    def test_get_file_list_basic(self):
        base_dir = self.dir_setup_data[0]['dir']
        file_listing = list_files(directory=base_dir)
        self.assertIsNotNone(file_listing)
        self.assertIsInstance(file_listing, dict)
        self.assertEqual(len(file_listing), 2)
        for file_with_full_path, file_meta_data in file_listing.items():
            self.assertIsNotNone(file_with_full_path)
            self.assertIsNotNone(file_meta_data)
            self.assertTrue(base_dir in file_with_full_path)
            self.assertTrue(file_with_full_path.endswith('txt'))
            self.assertIsNone(file_meta_data['size'])
            self.assertIsNone(file_meta_data['md5'])
            self.assertIsNone(file_meta_data['sha256'])

    def test_get_file_list_basic_with_callback(self):
        base_dir = self.dir_setup_data[0]['dir']
        file_listing = list_files(directory=base_dir, progress_callback_function=dir_list_callback_strips_metadata)
        self.assertIsNotNone(file_listing)
        self.assertIsInstance(file_listing, dict)
        self.assertEqual(len(file_listing), 2)
        for file_with_full_path, file_meta_data in file_listing.items():
            self.assertIsNotNone(file_with_full_path)
            self.assertIsNotNone(file_meta_data)
            self.assertTrue(base_dir in file_with_full_path)
            self.assertTrue(file_with_full_path.endswith('txt'))
            self.assertFalse('size' in file_meta_data)
            self.assertFalse('md5' in file_meta_data)
            self.assertFalse('sha256' in file_meta_data)

    def test_get_file_list_basic_with_file_sizes(self):
        base_dir = self.dir_setup_data[0]['dir']
        file_listing = list_files(directory=base_dir, include_size=True)
        for file_with_full_path, file_meta_data in file_listing.items():
            self.assertIsNotNone(file_with_full_path)
            self.assertIsNotNone(file_meta_data)
            self.assertTrue(base_dir in file_with_full_path)
            self.assertTrue(file_with_full_path.endswith('txt'))
            self.assertIsNotNone(file_meta_data['size'])
            self.assertIsNone(file_meta_data['md5'])
            self.assertIsNone(file_meta_data['sha256'])
            self.assertIsInstance(file_meta_data['size'], int)
            self.assertTrue(file_meta_data['size'] > 0)

    def test_get_file_list_basic_with_md5_checksums(self):
        base_dir = self.dir_setup_data[0]['dir']
        file_listing = list_files(directory=base_dir, calc_md5_checksum=True)
        self.assertIsNotNone(file_listing)
        self.assertIsInstance(file_listing, dict)
        self.assertEqual(len(file_listing), 2)
        for file_with_full_path, file_meta_data in file_listing.items():
            self.assertIsNotNone(file_with_full_path)
            self.assertIsNotNone(file_meta_data)
            self.assertTrue(base_dir in file_with_full_path)
            self.assertTrue(file_with_full_path.endswith('txt'))
            self.assertIsNone(file_meta_data['size'])
            self.assertIsNotNone(file_meta_data['md5'])
            self.assertIsNone(file_meta_data['sha256'])
            self.assertIsInstance(file_meta_data['md5'], str)
            self.assertTrue(len(file_meta_data['md5']) > 0)

    def test_get_file_list_basic_with_sha256_checksums(self):
        base_dir = self.dir_setup_data[0]['dir']
        file_listing = list_files(directory=base_dir, calc_sha256_checksum=True)
        self.assertIsNotNone(file_listing)
        self.assertIsInstance(file_listing, dict)
        self.assertEqual(len(file_listing), 2)
        for file_with_full_path, file_meta_data in file_listing.items():
            self.assertIsNotNone(file_with_full_path)
            self.assertIsNotNone(file_meta_data)
            self.assertTrue(base_dir in file_with_full_path)
            self.assertTrue(file_with_full_path.endswith('txt'))
            self.assertIsNone(file_meta_data['size'])
            self.assertIsNone(file_meta_data['md5'])
            self.assertIsNotNone(file_meta_data['sha256'])
            self.assertIsInstance(file_meta_data['sha256'], str)
            self.assertTrue(len(file_meta_data['sha256']) > 0)

    def test_get_file_list_recursively_with_file_sizes(self):
        base_dir = self.dir_setup_data[0]['dir']
        file_listing = list_files(directory=base_dir, include_size=True, recurse=True)
        print('>>> file_listing={}'.format(json.dumps(file_listing)))
        self.assertIsNotNone(file_listing)
        self.assertIsInstance(file_listing, dict)
        self.assertEqual(len(file_listing), 8)
        for file_with_full_path, file_meta_data in file_listing.items():
            self.assertIsNotNone(file_with_full_path)
            self.assertIsNotNone(file_meta_data)
            self.assertTrue(base_dir in file_with_full_path)
            self.assertTrue(file_with_full_path.endswith('txt'))
            self.assertIsNotNone(file_meta_data['size'])
            self.assertIsNone(file_meta_data['md5'])
            self.assertIsNone(file_meta_data['sha256'])
            self.assertIsInstance(file_meta_data['size'], int)
            self.assertTrue(file_meta_data['size'] > 0)

    def test_get_file_list_recursively_with_everything(self):
        base_dir = self.dir_setup_data[0]['dir']
        file_listing = list_files(directory=base_dir, include_size=True, recurse=True, calc_md5_checksum=True, calc_sha256_checksum=True)
        print('>>> file_listing={}'.format(json.dumps(file_listing)))
        self.assertIsNotNone(file_listing)
        self.assertIsInstance(file_listing, dict)
        self.assertEqual(len(file_listing), 8)
        for file_with_full_path, file_meta_data in file_listing.items():
            self.assertIsNotNone(file_with_full_path)
            self.assertIsNotNone(file_meta_data)
            self.assertTrue(base_dir in file_with_full_path)
            self.assertTrue(file_with_full_path.endswith('txt'))
            self.assertIsNotNone(file_meta_data['size'])
            self.assertIsNotNone(file_meta_data['md5'])
            self.assertIsNotNone(file_meta_data['sha256'])
            self.assertIsInstance(file_meta_data['size'], int)
            self.assertTrue(file_meta_data['size'] > 0)
            self.assertIsInstance(file_meta_data['md5'], str)
            self.assertTrue(len(file_meta_data['md5']) > 0)
            self.assertIsInstance(file_meta_data['sha256'], str)
            self.assertTrue(len(file_meta_data['sha256']) > 0)


def file_read_callback(
    path_to_file: str,
    current_chunk_sequence_number: int,
    chunk_size: int,
    content: str,
    return_object: object,
):
    print()
    if return_object is None:
        return_object = ''
    print('file_read_callback(): path_to_file                  = {}'.format(path_to_file))
    print('file_read_callback(): current_chunk_sequence_number = {}'.format(current_chunk_sequence_number))
    print('file_read_callback(): chunk_size                    = {}'.format(chunk_size))
    print('file_read_callback(): content size                  = {}'.format(len(content)))
    print('file_read_callback(): return_object                 = {}'.format(return_object))
    return '{}{}'.format(copy.deepcopy(return_object), copy.deepcopy(content[0:5]))


class TestFileIoReadFunctions(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        print()
        self.tmp_dir = create_temp_directory()
        # Create a small file
        self.small_file = '{}{}small_file.txt'.format(self.tmp_dir, os.sep)
        self.small_data = generate_random_string(length=128)
        with open(self.small_file, 'w') as f:
            f.write(self.small_data)
        # Create a large file ()
        self.large_data = generate_random_string(length=20000)
        self.large_file = '{}{}large_file.txt'.format(self.tmp_dir, os.sep)
        with open(self.large_file, 'w') as f:
            f.write(self.large_data)
        print('SETUP COMPLETE')
        print()
        
    def tearDown(self):
        print()
        print()
        print('DELETING DIRECTORIES')
        delete_directory(dir=self.tmp_dir)
        print('* Deleted directory "{}"'.format(self.tmp_dir))
        print()
        print()

    def test_read_small_file(self):
        result = read_text_file(self.small_file)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 128)

    def test_read_large_file(self):
        result = read_text_file(path_to_file=self.large_file)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 20000)

    def test_read_large_file_with_callback(self):
        result = read_large_text_file(path_to_file=self.large_file, callback_func=file_read_callback, chunk_size=5000)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 20)


class TestFileIoCopyFunctions(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        print()
        self.tmp_dir = create_temp_directory()
        # Create a small file
        self.small_file = '{}{}small_file.txt'.format(self.tmp_dir, os.sep)
        self.small_data = generate_random_string(length=128)
        with open(self.small_file, 'w') as f:
            f.write(self.small_data)
        print('SETUP COMPLETE')
        print()
        
    def tearDown(self):
        print()
        print()
        print('DELETING DIRECTORIES')
        delete_directory(dir=self.tmp_dir)
        print('* Deleted directory "{}"'.format(self.tmp_dir))
        print()
        print()

    def test_read_small_file_keep_original_file_name(self):
        dest_dir = create_temp_directory()
        dest_file_result = copy_file(source_file_path=self.small_file, destination_directory=dest_dir)
        source_files = list_files(directory=self.tmp_dir, calc_sha256_checksum=True, include_size=True)
        dest_files = list_files(directory=dest_dir, calc_sha256_checksum=True, include_size=True)
        source_checksum = 'wrong'
        source_size = -1
        for source_file, source_file_meta_data in source_files.items():
            self.assertEqual(source_file, self.small_file)
            source_checksum = source_file_meta_data['sha256']
            source_size = source_file_meta_data['md5']
        dest_checksum = 'wrong-again'
        dest_size = -2
        for dest_file, dest_file_meta_data in dest_files.items():
            self.assertEqual(dest_file, dest_file_result)
            dest_checksum = dest_file_meta_data['sha256']
            dest_size = dest_file_meta_data['md5']
        self.assertEqual(source_checksum, dest_checksum)
        self.assertEqual(source_size, dest_size)
        delete_directory(dir=dest_dir)

    def test_read_small_file_new_name(self):
        dest_dir = create_temp_directory()
        dest_file_result = copy_file(source_file_path=self.small_file, destination_directory=dest_dir, new_name='target_file.text')
        source_files = list_files(directory=self.tmp_dir, calc_sha256_checksum=True, include_size=True)
        dest_files = list_files(directory=dest_dir, calc_sha256_checksum=True, include_size=True)
        source_checksum = 'wrong'
        source_size = -1
        for source_file, source_file_meta_data in source_files.items():
            self.assertEqual(source_file, self.small_file)
            source_checksum = source_file_meta_data['sha256']
            source_size = source_file_meta_data['md5']
        dest_checksum = 'wrong-again'
        dest_size = -2
        for dest_file, dest_file_meta_data in dest_files.items():
            self.assertTrue('target_file.text' in dest_file)
            self.assertEqual(dest_file, dest_file_result)
            dest_checksum = dest_file_meta_data['sha256']
            dest_size = dest_file_meta_data['md5']
        self.assertEqual(source_checksum, dest_checksum)
        self.assertEqual(source_size, dest_size)
        delete_directory(dir=dest_dir)



if __name__ == '__main__':
    unittest.main()
