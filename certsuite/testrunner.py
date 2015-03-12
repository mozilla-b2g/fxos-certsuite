import os
import sys
import json
from collections import OrderedDict

import mozprocess
from mozfile import TemporaryDirectory
from reportmanager import ReportManager
from logmanager import LogManager
from mozlog.structured import structuredlog, handlers, formatters, set_default_logger

stdio_handler = handlers.StreamHandler(sys.stderr,
                                       formatters.MachFormatter())

class TestRunner(object):
    def __init__(self, args, config, logger):
        self.args = args
        self.config = config
        self.logger = logger

    def iter_suites(self):
        '''
        Iterate over test suites and groups of tests that are to be run. Returns
        tuples of the form (suite, [test_groups]) where suite is the name of a
        test suite and [test_groups] is a list of group names to run in that suite,
        or the empty list to indicate all tests.
        '''
        if not self.args.tests:
            tests = self.config["suites"].keys()
        else:
            tests = self.args.tests

        d = OrderedDict()
        for t in tests:
            v = t.split(":", 1)
            suite = v[0]
            if suite not in d:
                d[suite] = []

            if len(v) == 2:
                #TODO: verify tests passed against possible tests?
                d[suite].append(v[1])

        for suite, groups in d.iteritems():
            yield suite, groups

    def run_suite(self, suite, groups, log_manager, report_manager):
        with TemporaryDirectory() as temp_dir:
            result_files, structured_path = self.run_test(suite, groups, temp_dir)

            for path in result_files:
                file_name = os.path.split(path)[1]
                log_manager.add_file(path, "%s/%s" % (suite, file_name))

            report_manager.add_subsuite_report(structured_path)

    def run_test(self, suite, groups, temp_dir):
        self.logger.info('Running suite %s' % suite)

        def on_output(line):
            written = False
            if line.startswith("{"):
                try:
                    data = json.loads(line.strip())
                    if "action" in data:
                        sub_logger.log_raw(data)
                        written = True
                except ValueError:
                    pass
            if not written:
                self.logger.process_output(proc.pid,
                                      line.decode("utf8", "replace"),
                                      command=" ".join(cmd))

        try:
            cmd, output_files, structured_path = self.build_command(suite, groups, temp_dir)

            self.logger.debug(cmd)
            self.logger.debug(output_files)

            env = dict(os.environ)
            env['PYTHONUNBUFFERED'] = '1'
            proc = mozprocess.ProcessHandler(cmd, env=env, processOutputLine=on_output)
            self.logger.debug("Process '%s' is running" % " ".join(cmd))
            #TODO: move timeout handling to here instead of each test?
            with open(structured_path, "w") as structured_log:
                sub_logger = structuredlog.StructuredLogger(suite)
                sub_logger.add_handler(stdio_handler)
                sub_logger.add_handler(handlers.StreamHandler(structured_log,
                                                              formatters.JSONFormatter()))
                proc.run()
                proc.wait()
            self.logger.debug("Process finished")

        except Exception:
            self.logger.error("Error running suite %s:\n%s" % (suite, traceback.format_exc()))
            raise
        finally:
            try:
                proc.kill()
            except:
                pass

        return output_files, structured_path

    def build_command(self, suite, groups, temp_dir):
        suite_opts = self.config["suites"][suite]

        subn = self.config.copy()
        del subn["suites"]
        subn.update({"temp_dir": temp_dir})

        cmd = [suite_opts['cmd']]

        log_name = "%s/%s_structured_%s.log" % (temp_dir, suite, "_".join(item.replace("/", "-") for item in groups))
        cmd.extend(["--log-raw=-"])

        if groups:
            cmd.extend('--include=%s' % g for g in groups)

        cmd.extend(item % subn for item in suite_opts.get("run_args", []))
        cmd.extend(item % subn for item in suite_opts.get("common_args", []))

        output_files = [log_name]
        output_files += [item % subn for item in suite_opts.get("extra_files", [])]

        return cmd, output_files, log_name



