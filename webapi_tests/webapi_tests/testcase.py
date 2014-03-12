import os

import mozdevice
from marionette import Marionette, MarionetteTestCase, MarionetteException

class MinimalTestCase(MarionetteTestCase):
    def __init__(self, *args, **kwargs):
        self.cert_test_app = None
        super(MinimalTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        super(MinimalTestCase, self).setUp()
        self.use_cert_app()

    def tearDown(self):
        self.close_cert_app()
        super(MinimalTestCase, self).tearDown()

    def use_cert_app(self):
        # app management is done in the system app
        self.marionette.switch_to_frame()
        # TODO: replace this with pkg_resources if we know that we'll be installing this as a package
        self.marionette.import_script(os.path.join(os.path.dirname(__file__), "app_management.js"))
        script = "GaiaApps.launchWithName('CertTest App');"
        try:
            # NOTE: if the app is already launched, this doesn't launch a new app, it will return
            # a reference to the existing app
            self.cert_test_app = self.marionette.execute_async_script(script, script_timeout=5000)
            self.assertTrue(self.cert_test_app, "Could not launch CertTest App")
            self.marionette.switch_to_frame(self.cert_test_app["frame"])
        except MarionetteException as e:
            self.instruct("Could not launch CertTest app automatically." \
                          "Please launch by hand.")
            iframes = self.marionette.execute_script("return document.getElementsByTagName('iframe').length")
            for i in range(0, iframes):
                self.marionette.switch_to_frame(i)
                if ("certtest" in self.marionette.get_url()):
                    return
                self.marionette.switch_to_frame()
            self.fail("Could not switch into CertTest App")
        except Exception as e:
            message = "Unexpected exception: %s" % e
            self.fail(message)
        self.assertTrue("certtest" in self.marionette.get_url())

    def manually_close_app(self):
        instruction = "Could not close CertTest app automatically. " \
                      "Please close the app manually by holding down the Home button " \
                      "and pressing the X above the CertTest app card."
        try:
            response = raw_input("\n=== INSTRUCTION ===\n%s\nWere you successful at closing the app? [Y/n]\n" % instruction) or 'y'
            while response not in ['y', 'n']:
                response = raw_input("Please enter 'y' or 'n': ") or 'y'
        except KeyboardInterrupt:
            self.fail("Test interrupted by user")
        if response == 'n':
            print "Must reboot"
            dm = mozdevice.DeviceManagerADB()
            dm.reboot(wait=True)
            self.instruct("Please unlock the lockscreen after device reboots")
            dm.forward("tcp:2828", "tcp:2828")
            self.marionette = Marionette()
            self.marionette.start_session()
            self.fail("Failed attempts at closing app.")

    def close_cert_app(self):
        # TODO: replace this with pkg_resources if we know that we'll be installing this as a package
        self.marionette.import_script(os.path.join(os.path.dirname(__file__), "app_management.js"))
        # app management is done in the system app
        self.marionette.switch_to_frame()
        if self.cert_test_app and "origin" in self.cert_test_app:
            try:
                script = "GaiaApps.kill('%s');" % self.cert_test_app["origin"]
                self.marionette.execute_async_script(script, script_timeout=5000)
                self.assertTrue('certtest' not in self.marionette.get_url())
            except MarionetteException as e:
                self.manually_close_app()
            except Exception as e:
                message = "Unexpected exception: %s" % e
                self.fail(message)
        else:
            self.manually_close_app()

    def instruct(self, message):
        response = None
        print("\n=== INSTRUCTION ===\n%s" % message)
        try:
            while response not in ["y", "n", ""]:
                response = raw_input("Were you successful? [Yn] ").lower()
        except (KeyboardInterrupt, EOFError):
            self.fail("Test interrupted by user")
        if response == "n":
            self.fail("Failed on step: %s" % message)

    def unplug_and_instruct(self, message):
        self.instruct("Unplug the phone.\n%s\nPlug the phone back in after you are done, "\
                      "and unlock the screen if necessary.\n" % message)
        dm = mozdevice.DeviceManagerADB()
        dm.forward("tcp:2828", "tcp:2828")
        self.marionette = Marionette()
        self.marionette.start_session()
        self.use_cert_app()
