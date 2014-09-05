# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


class DeviceStorageTestCommon(object):

    def is_sdcard_available(self):
        ret_check_sdcard = self.marionette.execute_async_script("""
        var request = window.wrappedJSObject.sdcard.available();
        var flag = false;

        request.onsuccess = function () {
            if (this.result == "available") {
                flag = true;
            } else if (this.result == "unavailable" ||
              this.result == "shared") {
                console.log("sdcard is either unavailable or " +
                            "usb storage is enabled")
                flag = false;
            }
            marionetteScriptFinished(flag);
        };
        request.onerror = function () {
            flag = this.error.name;
            console.log("Unable to get the space used by the sdcard " + flag)
            marionetteScriptFinished(flag);
        };
        """, script_timeout=10000)
        return ret_check_sdcard

    def add_namedfile_sdcard(self, file_name, file_contents):
        ret_namedfile_sdcard = self.marionette.execute_async_script("""
        var file_name = arguments[0];
        var file_contents = arguments[1]

        //create a file with contents
        var file = new Blob([file_contents], {type: "text/plain"});
        var request = window.wrappedJSObject.sdcard.addNamed(file, file_name);

        request.onsuccess = function () {
            var name = this.result;
            marionetteScriptFinished(true);
        };
        request.onerror = function () {
            console.log("Unable to write the file: " + this.error.name);
            marionetteScriptFinished("Unable to write the file: " + this.error.name);
        };
        """, script_args=[file_name, file_contents])
        return ret_namedfile_sdcard

    def get_file_sdcard(self, file_name):
        get_filename_sdcard = self.marionette.execute_async_script("""
        var file_name = arguments[0];
        var request = window.wrappedJSObject.sdcard.get(file_name);

        request.onsuccess = function () {
            //file name will be stored in this.result.name
            marionetteScriptFinished(true);
        };
        request.onerror = function () {
            console.log("Unable to get the file: " + this.error.name);
            marionetteScriptFinished(false);
        };
        """, script_args=[file_name])
        return get_filename_sdcard

    def delete_file_sdcard(self, file_name):
        ret_file_delete_sdcard = self.marionette.execute_async_script("""
        var delete_file = arguments[0];
        var request = window.wrappedJSObject.sdcard.delete(delete_file);
        request.onsuccess = function () {
            marionetteScriptFinished(true);
        }
        request.onerror = function (error) {
            console.log('Unable to remove the file: ' + this.error.name);
            marionetteScriptFinished('Unable to remove the file: ' + this.error.name);
        }
        """, script_args=[file_name])
        return ret_file_delete_sdcard

    def enumerate_files_sdcard(self):
        ret_filelist_sdcard_unicode = self.marionette.execute_async_script("""
        var cursor = window.wrappedJSObject.sdcard.enumerate();
        var file_list = [];

        cursor.onsuccess = function () {
            if (this.result) {
                var file = this.result;
                file_list.push(file.name);

                // Once we found a file we check if there are other results
                // Then we move to the next result, which calls the cursor
                // success possibly with the next file as result.
                this.continue();
            } else {
                marionetteScriptFinished(file_list);
            }
        };
        """, script_timeout=20000)
        return ret_filelist_sdcard_unicode
