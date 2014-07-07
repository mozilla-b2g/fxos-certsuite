# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from collections import defaultdict

from mozlog.structured import reader
from py.xml import html, raw

here = os.path.split(__file__)[0]

class HTMLBuilder(object):
    def make_report(self, time, summary_results, subsuite_results):
        self.time = time
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
            style
        )

    def make_body(self):
        body_parts = [html.div(
            html.h1("FirefoxOS Certification Suite Report"),
            html.p("Run at %s" % self.time.strftime("%Y-%m-%d %H:%M:%S"))
            )]
        if self.summary_results.has_errors:
            body_parts.append(html.h2("Errors During Run"))
            body_parts.append(self.make_errors_table(self.summary_results.errors))
        body_parts.append(self.make_result_table())
        return html.body(body_parts)

    def make_errors_table(self, errors):
        rows = []
        for error in errors:
            rows.append(html.tr(
                html.td(error["level"],
                        class_="log_%s" % error["level"]),
                html.td(error.get("message", ""))
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
        for result in results:
            details_link = "%s/report.html" % result.name
            cells = [html.td(result.name)]
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

            if result.is_pass:
                cells.append(html.td())
            else:
                cells.append(html.td(
                    html.a("details",
                           href=details_link),
                    class_="details"
                ))
            rv.append(html.tr(cells))

        return rv

def make_report(time, summary_results, subsuite_results):
    doc = HTMLBuilder().make_report(time, summary_results, subsuite_results)

    return u"<!DOCTYPE html>\n" + doc.unicode(indent=2)
