import os

import fxos_appgen
import mozdevice

from marionette import MarionetteException

class CertAppMixin(object):
    app_name = "CertTest App"
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
        script = "GaiaApps.launchWithName('%s');" % CertAppMixin.app_name

        try:
            # NOTE: if the app is already launched, this doesn't
            # launch a new app, it will return a reference to the
            # existing app
            self.app = self.marionette.execute_async_script(
                script, script_timeout=CertAppMixin.timeout)
            self.assertTrue(self.app, "Could not launch %s" % CertAppMixin.app_name)
            self.marionette.switch_to_frame(self.app["frame"])
        except MarionetteException as e:
            self.instruct("Could not launch %s automatically. "
                          "Please launch by hand." % CertAppMixin.app_name)
            iframes = self.marionette.execute_script(
                "return document.getElementsByTagName('iframe').length")
            for i in range(0, iframes):
                self.marionette.switch_to_frame(i)
                if "certtest" in self.marionette.get_url():
                    return
                self.marionette.switch_to_frame()
            self.fail("Could not switch into %s" % CertAppMixin.app_name)
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
            self.fail("%s did not load in time" % CertAppMixin.app_name)

        self.assertTrue("certtest" in self.marionette.get_url())

        # Request that screen never dims or switch off.  Acquired wake locks
        # are implicitly released when the window object is closed or
        # destroyed.
        self.marionette.execute_script("""
            var wakeLock = window.navigator.requestWakeLock("screen");
            wakeLock.unlock();
            """)

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
        instruction = "Could not close %s automatically. " \
                      "Please close the app manually by holding down the Home button " \
                      "and pressing the X above the %s card." % \
                      (CertAppMixin.app_name, CertAppMixin.app_name)
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

    def install_cert_app(self):
        fxos_appgen.generate_app(CertAppMixin.app_name,
                                 install=True, version="1.3",
                                 all_perm=True,
                                 marionette=getattr(self, "marionette", None))

    # Issue filed: https://github.com/mozilla-b2g/fxos-appgen/issues/7
    def is_app_installed(self):
        installed_app_name = CertAppMixin.app_name.lower().replace(" ", "-")
        dm = mozdevice.DeviceManagerADB()
        return dm.dirExists("/data/local/webapps/%s" % installed_app_name)
