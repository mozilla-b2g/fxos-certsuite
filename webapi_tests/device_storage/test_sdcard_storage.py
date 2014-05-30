# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from semiauto import TestCase


class TestSDcardStorage(TestCase):

    def setUp(self):
        super(TestSDcardStorage, self).setUp()
        self.marionette.execute_script("""
            window.wrappedJSObject.sdcard =navigator.getDeviceStorage("sdcard")
        """)

    def test_add_delete_file(self):
        self.instruct("About to test sdcard add/delete files functionality; "
                      "make sure that USB storage is disabled on phone")
        check_sdcard = """
            var request = window.wrappedJSObject.sdcard.available();
            var flag = false;

            request.onsuccess = function () {
                if (this.result == "available") {
                    flag = true;
                } else if ((this.result == "unavailable") ||
                  (this.result == "shared")) {
                    console.log("sdcard is either unavailable or " +
                                "usb storage is enabled")
                    //sdcard is either unavailable or usb storage is enabled
                    flag = false;
                }
                marionetteScriptFinished(flag);
            };
            request.onerror = function () {
                flag = this.error;
                console.log("Unable to get the space used by the sdcard " +
                             this.error)
                marionetteScriptFinished(flag);
            };
        """
        ret_check_sdcard = self.marionette.execute_async_script(check_sdcard,
                           script_timeout=10000)
        self.assertTrue(ret_check_sdcard, "Unable to get the space used by "
                        "sdcard")

        #add file with contents to sdcard
        file_name = self.prompt("Please enter a file name to be added to "
                                "sdcard storage")
        if file_name is None:
            self.fail("Must enter a file name")
        file_contents = self.prompt("Please enter contents to be stored "
                                    "in the file \'%s\' " % file_name)
        add_namedfile_sdcard = """
            var file_name = arguments[0];
            var file_contents = arguments[1];

            //create a file with contents
            var file   = new Blob([file_contents], {type: "text/plain"});
            var request = window.wrappedJSObject.sdcard.addNamed(file,
                                                                 file_name);

            request.onsuccess = function () {
                var name = this.result;
                marionetteScriptFinished(true);
            };
            request.onerror = function () {
                console.log("Unable to write the file: " + this.error);
                marionetteScriptFinished(this.error);
            };
        """

        ret_add_namedfile_sdcard = self.marionette.execute_async_script(
                                   add_namedfile_sdcard,
                                   script_args=[file_name, file_contents])
        self.assertTrue(ret_add_namedfile_sdcard, "Unabled to write the file")

        #get the recently added file
        get_filename_sdcard = """
            var file_name = arguments[0];
            var name = false;
            var request = window.wrappedJSObject.sdcard.get(file_name);

            request.onsuccess = function () {
                name = this.result.name;
                marionetteScriptFinished(name);
            };
            request.onerror = function () {
                console.log("Unable to get the file: " + this.error);
                marionetteScriptFinished(name);
            };
        """
        ret_filename_path_sdcard = self.marionette.execute_async_script(
                                  get_filename_sdcard, script_args=[file_name])
        #checks if the recently added file exist in sdcard
        self.failIfEqual(ret_filename_path_sdcard, False, "Unable to get the "
                         "file")
        #extract the file name
        ret_file_name = ret_filename_path_sdcard.split("/")[-1]
        self.assertEqual(ret_file_name, file_name, "Unable to get the recently"
                         " added file from sdcard")

        #enumerate all the files from sdcard
        enumerate_files = """
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
                }
                else
                {
                    marionetteScriptFinished(file_list);
                }
            };
        """
        filelist_sdcard_unicode = self.marionette.execute_async_script(
                                  enumerate_files, script_timeout=20000)
        self.failIfEqual(0, len(filelist_sdcard_unicode), "There should be at "
                         "least one recently added file")

        #remove unicode and get filename
        sdcard_filelist = [str(name) for name in filelist_sdcard_unicode]
        filenames = ""
        for item in sdcard_filelist:
            filenames = (filenames + (item.split("/")[-1]) + ",")

        delete_file = self.prompt("Following files are available in sdcard."
                                  "Please enter a file name to be deleted "
                                  "from this list : \'%s\'" % filenames)

        delete_file_sdcard = """
            var delete_file = arguments[0];

            var request = window.wrappedJSObject.sdcard.delete(delete_file);

            request.onsuccess = function () {
            marionetteScriptFinished(true);
        }
            request.onerror = function (error) {
            console.log('Unable to remove the file: ' + this.error);
            marionetteScriptFinished(false);
        }
        """

        filename_path_sdcard = self.marionette.execute_async_script(
                               delete_file_sdcard, script_args=[delete_file])
        self.assertTrue(filename_path_sdcard, "Unable to delete file")

        #enumerate remaining files
        remaining_files_unicode = self.marionette.execute_async_script(
                                  enumerate_files, script_timeout=20000)

        #remove unicode and get filename
        remaining_filelist = [str(name) for name in remaining_files_unicode]
        rem_filenames = ""
        for item in remaining_filelist:
            rem_filenames = (rem_filenames + (item.split("/")[-1]) + ",")

        self.confirm("Please confirm if the deleted file is "
                     "not available in list : \'%s\'" % rem_filenames)
