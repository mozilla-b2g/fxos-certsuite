import os

from marionette import MarionetteTestCase, MarionetteException

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
                self.instruct("Could not close CertTest app automatically." \
                          "Please close by hand.")
            except Exception as e:
                message = "Unexpected exception: %s" % e
                self.fail(message)
        else:
            self.instruct("Could not close CertTest app automatically." \
                          "Please close by hand.")

    def instruct(self, message):
        response = None
        try:
            response = raw_input("\n=== INSTRUCTION ===\n%s\nWere you successful? [y/n]\n" % message)
            while response not in ['y', 'n']:
                response = raw_input("Please enter 'y' or 'n': ")
        except KeyboardInterrupt:
            self.fail("Test interrupted by user")
        if response == 'n':
            self.fail("Failed on step: %s" % message)
