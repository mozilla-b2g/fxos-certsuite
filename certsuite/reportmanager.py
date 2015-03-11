import os
import sys
import report
import zipfile
import mozprocess
from mozlog.structured import get_default_logger
from datetime import datetime
from mozfile import TemporaryDirectory

_index_header =  '''
.. FirefoxOS Certification Testsuite Report master file, created by
   sphinx-quickstart on Fri Apr 25 14:32:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

FirefoxOS Certification Testsuite Report
=================================

Tests and tools to verify the functionality and characteristics of
Firefox OS on real devices.

Contents:

.. toctree::
   :maxdepth: 1
'''
_index_footer = '''


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
'''
class ReportManager(object):
    def __init__(self, config):
        self.config = config
        self.zip_file = None
        self.subsuite_results = []
        self.structured_path = None
        self.logger = get_default_logger()
        self.index_content = '\n   summary\n'
        self.temp_dir = TemporaryDirectory()

    def setup_report(self, zip_file = None, 
        subsuite_results = None, 
        structured_path = None):
        self.time = datetime.now()
        self.zip_file = zip_file
        self.subsuite_results = subsuite_results
        self.structured_path = structured_path

    def __enter__(self):
        self.temp_obj = TemporaryDirectory()
        self.temp_dir = self.temp_obj.__enter__()
        self.encoding = sys.getdefaultencoding()
        reload(sys)
        sys.setdefaultencoding('utf8')
        return self

    def __exit__(self, *args, **kwargs):
        self.add_summary_report(self.structured_path)
        sys.setdefaultencoding(self.encoding)
        self.temp_obj.__exit__(*args)

    def runcmd(self, cmd):
        env = dict(os.environ)
        env['PYTHONUNBUFFERED'] = '1'

        def on_output(line):
            self.logger.process_output(proc.pid,
                  line.decode("utf8", "replace"),
                  command=" ".join(cmd))

        try:
            self.logger.debug("Process '%s' is running" % " ".join(cmd))
            proc = mozprocess.ProcessHandler(cmd, env=env, processOutputLine=on_output)
            proc.run()
            proc.wait()
        except Exception:
            self.logger.error("Error running:\n%s\n%s" % (" ".join(cmd), traceback.format_exc()))
            raise
        finally:
            try:
                proc.kill()
            except:
                pass

    def add_subsuite_report(self, path):
        results = report.parse_log(path)
        self.subsuite_results.append(results)
        html_str = report.subsuite.make_report(results)
        path = "%s/report.html" % results.name
        self.zip_file.writestr(path, html_str)

        report_path = self.temp_dir + os.sep + 'report' + os.sep
        # generate subsuite 
        os.makedirs(os.path.dirname(report_path + path))
        with open(report_path + path, 'w') as f:
            f.write(html_str)
        rstname = report_path + results.name + '.rst'
        cmd = ['pandoc', report_path + path, '-o', rstname]
        self.runcmd(cmd)

        # add report subsuite entry
        self.index_content = self.index_content + '   ' + results.name + '\n'

    def add_summary_report(self, path):
        if self.structured_path == None:
            return

        summary_results = report.parse_log(path)
        html_str = report.summary.make_report(self.time,
                                              summary_results,
                                              self.subsuite_results)
        path = "report.html"
        self.zip_file.writestr(path, html_str)

        if self.subsuite_results == []:
            # no test suite ran, just return and not generate report
            return

        report_path = self.temp_dir + os.sep + 'report' + os.sep
        # generate summary 
        with open(report_path + path, 'w') as f:
            f.write(html_str)
        cmd = ['pandoc', report_path + path, '-o', report_path + 'summary.rst']
        self.runcmd(cmd)

        # generate report index file
        contents = [_index_header, self.index_content, _index_footer]
        with open(report_path + 'index.rst', 'w') as f:
            f.write('\n'.join(contents))

        # copy sphinx template to temp folder
        template_path = os.sep.join([os.path.dirname(__file__) , 'static', 'report','']) 
        cmd = ['cp', '-R', template_path, self.temp_dir]
        self.runcmd(cmd)

        # generate report pdf
        cwd = os.getcwd()
        os.chdir(report_path)
        cmd = ['make', 'latexpdf']
        self.runcmd(cmd)

        # put report pdf to zip
        pdf_path = 'report.pdf'
        build_path = report_path + os.sep.join(['_build', 'latex', 'FirefoxOSCertificationTestsuiteReport.pdf'])
        self.zip_file.write(build_path, pdf_path)
        os.chdir(cwd)
