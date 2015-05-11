# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import zipfile
import os
import time

from datetime import datetime

from mozlog.structured import get_default_logger

class LogManager(object):
    def __init__(self):
        self.time = datetime.now()
        self.structured_path = "run.log"
        self.zip_path = 'firefox-os-certification_%s.zip' % (time.strftime("%Y%m%d%H%M%S"))
        self.structured_file = None
        self.subsuite_results = []

    def add_file(self, path, file_obj):
        self.zip_file.write(path, file_obj)

    def __enter__(self):
        self.zip_file = zipfile.ZipFile(self.zip_path, 'w', zipfile.ZIP_DEFLATED)
        self.structured_file = open(self.structured_path, "w")
        return self

    def __exit__(self, ex_type, ex_value, tb):
        args = ex_type, ex_value, tb
        if ex_type in (SystemExit, KeyboardInterrupt):
            logger = get_default_logger()
            logger.info("Testrun interrupted")
        try:
            self.structured_file.__exit__(*args)
            self.zip_file.write(self.structured_path)
        finally:
            try:
                os.unlink(self.structured_path)
            finally:
                self.zip_file.__exit__(*args)
