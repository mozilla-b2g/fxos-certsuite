import os
from collections import defaultdict

from mozlog.structured import reader
from py.xml import html, raw

here = os.path.split(__file__)[0]

result_status = dict((v,k) for k,v in
                     enumerate(["PASS", "FAIL", "OK", "ERROR", "TIMEOUT", "CRASH"]))

def is_regression(data):
    if "expected" not in data:
        return False

    return result_status[data["status"]] > result_status[data["expected"]]

class LogHandler(reader.LogHandler):
    def __init__(self):
        self.suite_name = None
        self.regressions = defaultdict(dict)

    def suite_start(self, data):
        self.suite_name = data["source"]

    def test_id(self, data):
        if isinstance(data["test"], unicode):
            return data["test"]
        else:
            return tuple(data["test"])

    def test_status(self, data):
        test_id = self.test_id(data)

        if is_regression(data):
            self.regressions[test_id][data["subtest"]] = data

    def test_end(self, data):
        test_id = self.test_id(data)

        if is_regression(data):
            self.regressions[test_id][None] = data

class HTMLBuilder(object):
    def make_report(self, suite_name, regressions):
        return html.html(
            self.make_head(suite_name),
            self.make_body(suite_name, regressions)
        )

    def make_head(self, suite_name):
        with open(os.path.join(here, "subsuite.css")) as f:
            style = html.style(raw(f.read()))

        return html.head(
            html.meta(charset="utf-8"),
            html.title("FirefoxOS Certification Suite Report: %s" % suite_name),
            style
        )

    def make_body(self, suite_name, regressions):
        return html.body(
            html.h1("FirefoxOS Certification Suite Report: %s" % suite_name),
            self.make_failure_table(regressions)
        )

    def make_failure_table(self, regressions):
        return html.table(
            html.thead(
                html.tr(
                    html.th("Parent Test"),
                    html.th("Subtest"),
                    html.th("Expected"),
                    html.th("Result"),
                    html.th("Message")
                )
            ),
            html.tbody(
                *self.make_table_rows(regressions)
            )
        )

    def make_table_rows(self, regressions):
        rv = []
        tests = sorted(regressions.keys())
        for i, test in enumerate(tests):
            test_data = regressions[test]
            cells, needs_subtest = self.make_test_name(test, test_data, i)
            for subtest in sorted(test_data.keys()):
                if needs_subtest:
                    cells.append(html.td(subtest))
                subtest_data = test_data[subtest]
                cells.extend([
                    html.td(subtest_data["expected"].title(),
                            class_="condition %s" % subtest_data["expected"]),
                    html.td(subtest_data["status"].title(),
                            class_="condition %s" % subtest_data["status"]),
                    html.td(subtest_data["message"],
                            class_="message")
                ])
                tr = html.tr(cells)
                rv.append(tr)
                cells = []
                needs_subtest = True
        return rv

    def test_string(self, test_id):
        if isinstance(test_id, unicode):
            return test_id
        else:
            return " ".join(test_id)

    def make_test_name(self, test, test_data, index):
        pos_cls = "even" if index % 2 else "odd"
        test_name = self.test_string(test)
        if len(test_data) == 1 and None in test_data.keys():
            return [html.td(test_name, colspan=2, class_="parent_test %s" % pos_cls)], False
        else:
            return [html.td(test_name, rowspan=len(test_data), class_="parent_test %s" % pos_cls)], True

def make_report(log_file):
    regression_handler = LogHandler()
    reader.handle_log(reader.read(log_file),
                      regression_handler)

    suite_name = regression_handler.suite_name
    regressions = regression_handler.regressions

    doc = HTMLBuilder().make_report(suite_name, regressions)

    return u"<!DOCTYPE html>\n" + doc.unicode(indent=2)

def create(input_path, output_path):
    with open(input_path) as f:
        data = make_report(f)

    with open(output_path, "w") as out_f:
        out_f.write(data)

if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as log_file:
        print make_report(log_file)
