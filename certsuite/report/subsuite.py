# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pkg_resources
import base64
import marionette.runner.mixins
import sys
import json

from py.xml import html, raw

here = os.path.split(__file__)[0]
rcname = marionette.runner.mixins.__name__

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
            style,
            html.style(raw(pkg_resources.resource_string(
                rcname, os.path.sep.join(['resources', 'htmlreport', 
                    'style.css']))),
                type='text/css'),
        )

    def make_body(self):
        body_parts = [
            html.script(raw(pkg_resources.resource_string(
                rcname, os.path.sep.join(['resources', 'htmlreport', 
                    'jquery.js']))),
                type='text/javascript'),
            html.script(raw(pkg_resources.resource_string(
                rcname, os.path.sep.join(['resources', 'htmlreport', 
                    'main.js']))),
                type='text/javascript'),
            html.a('#', href='http://mozilla.org', id='tabzilla'),
            html.h1("FirefoxOS Certification Suite Report: %s" 
                % self.results.name),
            ]

        if self.results.has_errors:
            body_parts.append(html.h2("Errors During Run"))
            body_parts.append(self.make_errors_table(self.results.errors))
        if self.results.has_regressions:
            body_parts.append(html.h2("Test Regressions"))
            body_parts.append(self.make_regression_table())
        if self.results.has('files'):
            body_parts.append(html.h2("Details information"))
            details = []
            files = self.results.get('files')
            for key in files.keys():
                href = '#'
                if key[-4:] == 'html' or key[-3:] == 'htm':
                    href = 'data:text/html;charset=utf-8;base64,%s' % base64.b64encode(files[key])
                else:
                    href = 'data:text/plain;charset=utf-8;base64,%s' % base64.b64encode(files[key])
                details.append(html.a(key, href=href, target='_blank'))
                details.append(' ')
            body_parts.extend(details)

        return html.body(body_parts)

    def make_errors_table(self, errors):
        rows = []
        for error in errors:
            rows.append(html.tr(
                html.td(error["level"],
                        class_="log_%s" % error["level"]),
                html.td(error.get("message", ""), class_='log')
            ))
        return html.table(rows, id_="errors")

    def make_regression_table(self):
        return html.table(
            html.thead(
                html.tr(
                    html.th("Parent Test", class_='sortable', col='parent'),
                    html.th("Subtest", class_='sortable', col='subtest'),
                    html.th("Expected", class_='sortable', col='expected'),
                    html.th("Result", class_='sortable', col='result'),
                ), id='results-table-head'
            ),
            html.tbody(*self.make_table_rows(),id='results-table-body'), 
            id='results-table'
        )

    def make_table_rows(self):
        regressions = self.results.regressions

        rv = []
        tests = sorted(regressions.keys())
        for i, test in enumerate(tests):
            odd_or_even = "even" if i % 2 else "odd"
            test_data = regressions[test]
            test_name = self.get_test_name(test, test_data)
            for subtest in sorted(test_data.keys()):
                cells = []
                sub_name = self.get_sub_name(test, test_data, subtest)

                subtest_data = test_data[subtest]
                cell_expected = self.get_cell_expected(subtest_data).upper()
                class_expected = self.get_class_expected(subtest_data)
                cell_message  = subtest_data.get("message", "")

                href = 'data:text/plain;charset=utf-8;base64,%s' % base64.b64encode(json.dumps(subtest_data))

                cells.extend([
                    html.td(test_name, class_="parent_test %s col-parent" % odd_or_even),
                    html.td(
                        html.a(sub_name, class_='test col-subtest', href=href, target='_blank'),
                        class_="parent_test %s" % odd_or_even),
                    html.td(cell_expected,
                            class_="condition col-expected %s %s" % (class_expected, odd_or_even)),
                    html.td(subtest_data["status"].title(),
                            class_="condition col-result %s %s" % (subtest_data["status"], odd_or_even))
                ])
                if cell_message == "":
                    rv.extend([
                        html.tr(cells, class_='passed result_table_row'),
                        html.tr(html.td(cell_message, class_='debug', colspan=5))
                        ])
                else:
                    rv.extend([
                        html.tr(cells, class_='error result_table_row'),
                        html.tr(html.td(html.div(cell_message, class_='log'), class_='debug', colspan=5))
                        ])
        return rv

    def get_cell_expected(self, subtest_data):
        if  'expected' in subtest_data:
            cell_expected = subtest_data["expected"].title()
        else:
            cell_expected = subtest_data["status"]
        return cell_expected

    def get_class_expected(self, subtest_data):
        if  'expected' in subtest_data:
            class_expected = subtest_data["expected"]
        else:
            class_expected = subtest_data["status"]
        return class_expected

    def test_string(self, test_id):
        if isinstance(test_id, unicode):
            return test_id
        else:
            return " ".join(test_id)

    def get_test_name(self, test, test_data):
        test_name = self.test_string(test)
        if len(test_data) == 1 and None in test_data.keys():
            start_index = test_name.find('.') + 1
            end_index = test_name.find('.' , start_index)
            test_name = test_name[start_index:end_index]
        return test_name

    def get_sub_name(self, test, test_data, subtest):
        test_name = self.test_string(test)
        if len(test_data) == 1 and None in test_data.keys():
            sub_start_index = test_name.rfind('.') + 1
            sub_name = test_name[sub_start_index:]
        else:
            if subtest:
                sub_name = subtest
            else:
                sub_name = 'parent'
        return sub_name

def make_report(results):
    doc = HTMLBuilder().make_report(results)
    with open('/tmp/test.html', 'w') as f:
        print 'write file /tmp/test.html'
        f.write(u"<!DOCTYPE html>\n" + doc.unicode(indent=2))
    return u"<!DOCTYPE html>\n" + doc.unicode(indent=2)

def make_file_report(path):
    from __init__ import parse_log
    results = parse_log(path)
    make_report(results)

if __name__ == "__main__":  
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    print make_file_report(sys.argv[1])
