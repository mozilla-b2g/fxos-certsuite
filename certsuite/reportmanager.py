import report
import zipfile

from datetime import datetime

class ReportManager(object):
    def __init__(self):
        self.zip_file = None
        self.subsuite_results = None
        self.structured_path = None

    def setup_report(self, zip_file = None, 
        subsuite_results = None, 
        structured_path = None):
        self.time = datetime.now()
        self.zip_file = zip_file
        self.subsuite_results = subsuite_results
        self.structured_path = structured_path

    def __enter__(self):
        return self

    def __exit__(self, *arfs, **kwargs):
        if self.structured_path:
            self.add_summary_report(self.structured_path)

    def add_subsuite_report(self, path):
        results = report.parse_log(path)
        self.subsuite_results.append(results)
        html_str = report.subsuite.make_report(results)
        path = "%s/report.html" % results.name
        self.zip_file.writestr(path, html_str)

    def add_summary_report(self, path):
        summary_results = report.parse_log(path)
        html_str = report.summary.make_report(self.time,
                                              summary_results,
                                              self.subsuite_results)
        path = "report.html"
        self.zip_file.writestr(path, html_str)
