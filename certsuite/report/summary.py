# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pkg_resources
import base64
import marionette.runner.mixins
from collections import defaultdict

from mozlog.structured import reader
from py.xml import html, raw

here = os.path.split(__file__)[0]
rcname = marionette.runner.mixins.__name__

class HTMLBuilder(object):
    def make_report(self, time, summary_results, subsuite_results, log_path):
        self.time = time
        self.log_path = log_path
        self.summary_results = summary_results
        self.subsuite_results = subsuite_results
        return html.html(
            self.make_head(),
            self.make_body()
        )

    def make_head(self):
        with open(os.path.join(here, "report.css")) as f:
            style = html.style(raw(f.read()))

        return html.head(
            html.meta(charset="utf-8"),
            html.title("FirefoxOS Certification Suite Report"),
            html.style(raw(pkg_resources.resource_string(
                rcname, os.path.sep.join(['resources', 'htmlreport', 
                    'style.css']))),
                type='text/css'),
            style
        )

    def make_body(self):
        body_parts = [html.div(
             html.script(raw(pkg_resources.resource_string(
                rcname, os.path.sep.join(['resources', 'htmlreport', 
                    'jquery.js']))),
                type='text/javascript'),
            html.script(raw(pkg_resources.resource_string(
                rcname, os.path.sep.join(['resources', 'htmlreport', 
                    'main.js']))),
                type='text/javascript'),
            html.h1("FirefoxOS Certification Suite Report"),
            html.p("Run at %s" % self.time.strftime("%Y-%m-%d %H:%M:%S"))
            )]
        if self.summary_results.has_errors:
            body_parts.append(html.h2("Errors During Run"))
            body_parts.append(self.make_errors_table(self.summary_results.errors))
        body_parts.append(self.make_result_table())

        details_log = ''
        with open(self.log_path, 'r') as f:
            details_log = f.read()
        href = 'data:text/plain;charset=utf-8;base64,%s' % base64.b64encode(details_log)
        body_parts.extend([
            html.h2("Details log information"),
            html.a(html.a('log', href=href, target='_blank'))
            ])
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

    def make_result_table(self):
        return html.table(
            html.thead(
                html.tr(
                    html.th("Subsuite"),
                    html.th("Subsuite Errors"),
                    html.th("Test Regressions"),
                    html.th("Details")
                )
            ),
            html.tbody(
                self.make_table_rows(self.subsuite_results)
            )
        )

    def make_table_rows(self, results):
        rv = []
        for key in results.keys():
            result = results[key]['results']
            details_link = 'data:text/html;charset=utf-8;base64,%s' % base64.b64encode(results[key]['html_str'])
            cells = [html.td(key)]
            if result.has_errors:
                cells.append(html.td(
                    len(result.errors),
                    class_="condition FAIL",
                ))
            else:
                cells.append(html.td("0",
                                     class_="condition PASS"))
            if result.has_regressions:
                num_regressions = sum(len(item) for item in result.regressions.itervalues())
                cells.append(html.td(num_regressions, class_="condition FAIL"))
            else:
                cells.append(html.td("0", class_="condition PASS"))

            cells.append(html.td(
                html.a("details", href=details_link, target='_blank'),
                class_="details"
            ))
            rv.append(html.tr(cells))

        return rv

def make_report(time, summary_results, subsuite_results, log_path):
    doc = HTMLBuilder().make_report(time, summary_results, subsuite_results, log_path)

    return u"<!DOCTYPE html>\n" + doc.unicode(indent=2)
