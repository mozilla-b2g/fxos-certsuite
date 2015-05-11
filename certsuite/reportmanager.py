# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import report
import zipfile
import sys
import os

from datetime import datetime

class ReportManager(object):
    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')
        self.zip_file = None
        self.subsuite_results = {}
        self.structured_path = None

    def setup_report(self, profile_path, zip_file = None,
        structured_path = None):
        self.time = datetime.now()
        self.zip_file = zip_file
        self.structured_path = structured_path
        self.profile_path = profile_path

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.structured_path:
            self.add_summary_report(self.structured_path)

    def add_subsuite_report(self, path, result_files):
        results = report.parse_log(path)

        # prepare embeded file data
        files_map = {}
        for path in result_files:
            if os.path.exists(path):
                file_name = os.path.split(path)[1]
                with open(path, 'r') as f:
                    files_map[file_name] = f.read()
                self.zip_file.writestr("%s/%s" % (results.name, os.path.basename(path)), files_map[file_name])
        results.set('files', files_map)

        self.subsuite_results[results.name] = {}
        self.subsuite_results[results.name]['files'] = files_map
        self.subsuite_results[results.name]['results'] = results
        self.subsuite_results[results.name]['html_str'] = report.subsuite.make_report(results)

        path = "%s/report.html" % results.name
        self.zip_file.writestr(path, self.subsuite_results[results.name]['html_str'])
        
        if results.has_regressions:
            return results.regressions
        else:
            return None

    def add_summary_report(self, path):
        summary_results = report.parse_log(path)
        html_str = report.summary.make_report(self.time,
                                              summary_results,
                                              self.subsuite_results,
                                              [path, self.profile_path])
        path = "report.html"
        self.zip_file.writestr(path, html_str)
