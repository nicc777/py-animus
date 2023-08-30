"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import os
import requests
import hashlib
import traceback


def download_files(urls: list, target_dir: str='/tmp', set_no_verify_ssl: bool=False)->list:
    files = list()
    for url in urls:
        outfile = '{}{}{}'.format(
            target_dir,
            os.sep,
            hashlib.sha256(url.encode('utf-8')).hexdigest()
        )
        if outfile not in files:
            r = None
            if set_no_verify_ssl is False:
                r = requests.get(url)
            else:
                r = requests.get(url, verify=False)
            if r is not None:
                with open(outfile, 'w') as f:
                    f.write(r.text)
                    files.append(outfile)
    return files

