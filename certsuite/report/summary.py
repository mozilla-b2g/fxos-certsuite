# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import cgi
import json
import pkg_resources
import base64
import marionette.runner.mixins
from collections import defaultdict

from mozlog.structured import reader
from py.xml import html, raw

here = os.path.split(__file__)[0]
rcname = marionette.runner.mixins.__name__

class HTMLBuilder(object):
    def make_report(self, time, summary_results, subsuite_results, logs):
        self.time = time
        self.logs = logs
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
        if self.logs:
            device_profile_object = None
            with open(self.logs[-1]) as f:
                device_profile_object = json.load(f)['result']['contact']
            device_profile = [html.h2('Device Information')]
            device_table = html.table()
            for key in device_profile_object:
                device_table.append(
                    html.tr(
                        html.td(key),
                        html.td(device_profile_object[key])
                    )
                )
                #device_profile.append(html.p("%s, %s"% (key, device_profile_object[key])))
            device_profile.append(device_table)
            body_parts.extend(device_profile);

        if self.summary_results.has_errors:
            body_parts.append(html.h2("Errors During Run"))
            body_parts.append(self.make_errors_table(self.summary_results.errors))
        body_parts.append(html.h2("Test Results"))
        body_parts.append(self.make_result_table())

        if self.logs:
            ulbody = [];
            for log_path in self.logs:
                details_log = ''
                with open(log_path, 'r') as f:
                    details_log = f.read()
                href = 'data:text/plain;charset=utf-8;base64,%s' % base64.b64encode(details_log)
                ulbody.append(html.li(html.a(os.path.basename(log_path), href=href, target='_blank')))
            device_profile_object = None
            body_parts.append(html.h2("Details log information"))
            body_parts.append(html.ul(ulbody))
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

    def make_result_table(self):
        return html.table(
            html.thead(
                html.tr(
                    html.th("Subsuite", class_='sortable', col='subsuite'),
                    html.th("Subsuite Errors"),
                    html.th("Test Executions"),
                    html.th("Details")
                )
            ),
            html.tbody(
                self.make_table_rows(self.subsuite_results),id='results-table-body'
            ), 
            id='results-table'
        )

    def make_table_rows(self, results):
        rv = []
        for key in results.keys():
            result = results[key]['results']
            cells = [html.td(key, class_="col-subsuite")]
            if result.has_errors:
                cells.append(html.td(
                    len(result.errors),
                    class_="condition FAIL col-subsuite",
                ))
            else:
                cells.append(html.td("0",
                                     class_="condition PASS"))
            style = ''
            if result.has_fails or result.has_errors:
                style = 'background-color: darkblue;'
            if result.has_regressions:
                num_regressions = sum(len(item) for item in result.regressions.itervalues())
                cells.append(html.td(num_regressions, class_="condition PASS", style=style))
            else:
                cells.append(html.td("0", class_="condition PASS"))
            
            details_link = 'data:text/html;charset=utf-8;base64,%s' % base64.b64encode(results[key]['html_str'])
            ulbody = [html.li(html.a("subsuite report", href=details_link, target='_blank'))]
            files = results[key]['files']
            for fname in files.keys():
                href = '%s/%s' % (key, fname)
                #if key[-4:] == 'html' or key[-3:] == 'htm':
                #    href = 'data:text/html;charset=utf-8;base64,%s' % base64.b64encode(files[key])
                #else:
                #    href = 'data:text/plain;charset=utf-8;base64,%s' % base64.b64encode(files[key])
                ulbody.append(html.li(html.a(fname, href=href, target='_blank')))
            
            cells.append(html.td(html.ul(ulbody), class_="details"))
            rv.append(html.tr(cells, class_='results-table-row'))

        return rv

def make_report(time, summary_results, subsuite_results, log_path):
    doc = HTMLBuilder().make_report(time, summary_results, subsuite_results, log_path)

    return u"<!DOCTYPE html>\n" + doc.unicode(indent=2)
