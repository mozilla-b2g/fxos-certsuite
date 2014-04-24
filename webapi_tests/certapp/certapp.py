import os

from marionette import MarionetteException


class CertAppMixin(object):
    app_management = os.path.join(os.path.dirname(__file__), "app_management.js")
    timeout = 5000  # ms

    def __init__(self, *args ,**kwargs):
        super(CertAppMixin, self).__init__(*args, **kwargs)
        self.app = None

    # App management is done in the system app, so switch to that
    # context.
    def _switch_to_app_management(self):
        self.marionette.switch_to_frame()
        # TODO(mdas): Replace this with pkg_resources if we know that
        # we'll be installing this as a package
        self.marionette.import_script(CertAppMixin.app_management)

    def use_cert_app(self):
        self._switch_to_app_management()
        script = "GaiaApps.launchWithName('CertTest App');"

        try:
            # NOTE: if the app is already launched, this doesn't
            # launch a new app, it will return a reference to the
            # existing app
            self.app = self.marionette.execute_async_script(
                script, script_timeout=CertAppMixin.timeout)
            self.assertTrue(self.app, "Could not launch CertTest App")
            self.marionette.switch_to_frame(self.app["frame"])
        except MarionetteException as e:
            self.instruct("Could not launch CertTest app automatically. "
                          "Please launch by hand.")
            iframes = self.marionette.execute_script(
                "return document.getElementsByTagName('iframe').length")
            for i in range(0, iframes):
                self.marionette.switch_to_frame(i)
                if "certtest" in self.marionette.get_url():
                    return
                self.marionette.switch_to_frame()
            self.fail("Could not switch into CertTest App")
        except Exception as e:
            message = "Unexpected exception: %s" % e
            self.fail(message)

        # TODO(ato): Replace this with Wait
        tries = 60
        while tries > 0:
            if 'blank' not in self.marionette.get_url():
                break
            time.sleep(1)
            tries -= 1
        if tries == 0:
            self.fail("CertTest app did not load in time")

        self.assertTrue("certtest" in self.marionette.get_url())

    def close_cert_app(self):
        if not self.app:
            return  

        self._switch_to_app_management()

        if "origin" in self.app:
            try:
                script = "GaiaApps.kill('%s');" % self.app["origin"]
                self.assertTrue("certtest" not in self.marionette.get_url(),
                                "Failed attempts at closing app")
                self.marionette.execute_async_script(
                    script, script_timeout=CertAppMixin.timeout)
            except MarionetteException as e:
                self.manually_close_app()
            except Exception as e:
                message = "Unexpected exception: %s" % e
                self.fail(message)
        else:
            self.manually_close_app()

    def manually_close_app(self):
        instruction = "Could not close CertTest app automatically. " \
                      "Please close the app manually by holding down the Home button " \
                      "and pressing the X above the CertTest app card."
        response = self.instruct(instruction)
        if response == 'n' or response == False:
            print "Must reboot"
            dm = mozdevice.DeviceManagerADB()
            dm.reboot(wait=True)
            self.instruct("Please unlock the lockscreen after device reboots")
            dm.forward("tcp:2828", "tcp:2828")
            self.marionette = Marionette()
            self.marionette.start_session()
            self.fail("Failed attempts at closing app.")
