# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from py.xml import html, raw

here = os.path.split(__file__)[0]

class HTMLBuilder(object):
    def make_report(self, results):
        self.results = results
        return html.html(
            self.make_head(),
            self.make_body()
        )

    def make_head(self):
        with open(os.path.join(here, "report.css")) as f:
            style = html.style(raw(f.read()))

        return html.head(
            html.meta(charset="utf-8"),
            html.title("FirefoxOS Certification Suite Report: %s" % self.results.name),
            style
        )

    def make_body(self):
        body_parts = [html.h1("FirefoxOS Certification Suite Report: %s" % self.results.name)]

        if self.results.has_errors:
            body_parts.append(html.h2("Errors During Run"))
            body_parts.append(self.make_errors_table(self.results.errors))
        if self.results.has_regressions:
            body_parts.append(html.h2("Test Regressions"))
            body_parts.append(self.make_regression_table())

        return html.body(
            body_parts
        )

    def make_errors_table(self, errors):
        rows = []
        for error in errors:
            rows.append(html.tr(
                html.td(error["level"],
                        class_="log_%s" % error["level"]),
                html.td(error.get("message", ""))
            ))
        return html.table(rows, id_="errors")

    def make_regression_table(self):
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
                *self.make_table_rows()
            )
        )

    def make_table_rows(self):
        regressions = self.results.regressions

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
                    html.td(subtest_data.get("message", ""),
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

def make_report(results):
    doc = HTMLBuilder().make_report(results)

    return u"<!DOCTYPE html>\n" + doc.unicode(indent=2)

if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as log_file:
        print make_report(log_file)
