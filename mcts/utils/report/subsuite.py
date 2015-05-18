# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import base64
import marionette.runner.mixins
import sys
import json
import cgi
import pickle

from py.xml import html, raw
from results import KEY_MAIN

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
            style
        )

    def make_body(self):
        body_parts = [
            html.h1("FirefoxOS Certification Suite Report: %s"
                % self.results.name),
            ]

        if self.results.has_errors:
            body_parts.append(html.h2("Errors During Run"))
            body_parts.append(self.make_errors_table(self.results.errors))
        if self.results.has_regressions:
            body_parts.append(html.h2("Test Regressions"))
            body_parts.append(self.make_regression_table())
        #if self.results.has('files'):
        #    body_parts.append(html.h2("Details information"))
        #    details = []
        #    files = self.results.get('files')
        #    for key in files.keys():
        #        href = '#'
        #        if key[-4:] == 'html' or key[-3:] == 'htm':
        #            href = 'data:text/html;charset=utf-8;base64,%s' % base64.b64encode(files[key])
        #        else:
        #            href = 'data:text/plain;charset=utf-8;base64,%s' % base64.b64encode(files[key])
        #        details.append(html.li(html.a(key, href=href, target='_blank')))
        #    body_parts.append(html.ul(details))

        return html.body(body_parts)

    def make_errors_table(self, errors):
        rows = []
        for error in errors:
            error_message = error.get("message", "")
            log = html.div(class_='log')
            for line in error_message.splitlines():
                separator = line.startswith(' ' * 10)
                if separator:
                    log.append(line[:80])
                else:
                    if line.lower().find("error") != -1 or line.lower().find("exception") != -1:
                        log.append(html.span(raw(cgi.escape(line)), class_='error'))
                    else:
                        log.append(raw(cgi.escape(line)))
                log.append(html.br())
            rows.append(html.tr(
                html.td(error["level"],
                        class_="log_%s" % error["level"]),
                html.td(log, class_='log')
            ))
        return html.table(rows, id_="errors")

    def make_regression_table(self):
        return html.table(
            html.thead(
                html.tr(
                    html.th("Parent Test", col='parent'),
                    html.th("Subtest", col='subtest'),
                    html.th("Expected", col='expected'),
                    html.th("Result", col='result'),
                ), id='results-table-head'
            ),
            html.tbody(*self.make_table_rows(), id='results-table-body'),
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
                cell_message = subtest_data.get("message", "")
                cell_status = subtest_data["status"]

                if cell_message != "":
                    try:
                        # if cell_message is dict obj, then it will be {'text': HTML_A_TEXT, 'href': HTML_A_HREF, 'target': HTML_A_TARGET}
                        link = pickle.loads(cell_message)
                        if 'text' in link and 'href' in link:
                            if 'target' in link:
                                cell_message = html.div(html.pre(html.a(link['text'], href=link['href'], target=link['target'])), class_='log')
                            else:
                                cell_message = html.div(html.pre(html.a(link['text'], href=link['href'])), class_='log')
                    except:
                        log = html.pre()
                        for line in cell_message.splitlines():
                            separator = line.startswith(' ' * 10)
                            if separator:
                                log.append(line[:80])
                            else:
                                if line.lower().find("error") != -1 or line.lower().find("exception") != -1:
                                    log.append(html.span(raw(cgi.escape(line)), class_='error'))
                                else:
                                    log.append(raw(cgi.escape(line)))
                        cell_message = html.div(log, class_='log')

                href = 'data:text/plain;charset=utf-8;base64,%s' % base64.b64encode(json.dumps(subtest_data))

                cells.extend([
                    html.td(test_name, class_="parent_test %s col-parent" % odd_or_even),
                    html.td(
                        html.a(sub_name, class_='test col-subtest', href=href, target='_blank'),
                        class_="parent_test %s" % odd_or_even),
                    html.td(cell_expected,
                        class_="condition col-expected %s %s" % (class_expected, odd_or_even)),
                    html.td(cell_status.title(),
                        class_="condition col-result %s %s" % (cell_status, odd_or_even))
                ])
                if cell_message == "":
                    rv.append(
                        html.tr(cells, class_='passed results-table-row %s %s' % (cell_status, odd_or_even))
                        )
                else:
                   rv.extend([
                        html.tr(cells, class_='error results-table-row %s %s' % (cell_status, odd_or_even)),
                        html.tr(html.td(cell_message, class_='debug {}'.format(odd_or_even), colspan=5))
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
        if len(test_data) == 1 and KEY_MAIN in test_data.keys():
            start_index = test_name.find('.') + 1
            end_index = test_name.find('.', start_index)
            test_name = test_name[start_index:end_index]
        return test_name

    def get_sub_name(self, test, test_data, subtest):
        test_name = self.test_string(test)
        if len(test_data) == 1 and KEY_MAIN in test_data.keys():
            sub_start_index = test_name.rfind('.') + 1
            sub_name = test_name[sub_start_index:]
        else:
            if subtest == KEY_MAIN:
                sub_name = 'parent'
            else:
                sub_name = subtest
        return sub_name


def make_report(results):
    doc = HTMLBuilder().make_report(results)
    return u"<!DOCTYPE html>\n" + doc.unicode(indent=2)


def make_file_report(path):
    from __init__ import parse_log
    results = parse_log(path)
    with open('/tmp/test.html', 'w') as f:
        print 'write file /tmp/test.html'
        f.write(make_report(results))

if __name__ == "__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    print make_file_report(sys.argv[1])
