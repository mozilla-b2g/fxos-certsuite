# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


class AppsTestCommon(object):
    def get_self(self):
        app = self.marionette.execute_async_script("""
        let request = navigator.mozApps.getSelf();
        request.onsuccess = function() {
            let result = {};
            result['manifest'] = request.result['manifest'];
            result['origin'] = request.result['origin'];
            marionetteScriptFinished(result);
        };
        request.onerror = function() {
            throw request.error.name;
        };
        """)
        self.assertIsNotNone(app, "mozApps.getSelf returned none")
        return app

    def get_all(self):
        applist = self.marionette.execute_async_script("""
        let request = navigator.mozApps.mgmt.getAll();
        request.onsuccess = function() {
            let resultlist = [];
            for (let i in request.result) {
                let result = {};
                result['manifest'] = request.result[i]['manifest'];
                result['origin'] = request.result[i]['origin'];
                resultlist.push(result);
            }
            marionetteScriptFinished(resultlist);
        };
        request.onerror = function() { throw request.error.name };
        """)
        self.assertIsNotNone(applist, "mozApps.mgmt.getAll returned none")
        return applist
