import os
import time

import mozdevice
from marionette import Marionette, MarionetteTestCase, MarionetteException

from certapp import CertAppMixin

class MinimalTestCase(MarionetteTestCase, CertAppMixin):
    def __init__(self, *args, **kwargs):
        self.cert_test_app = None
        # Use a new marionette object instead of relying on older references
        self.marionette = Marionette
        super(MinimalTestCase, self).__init__(self.marionette, **kwargs)

    def setUp(self):
        super(MinimalTestCase, self).setUp()
        self.use_cert_app()

    def tearDown(self):
        self.close_cert_app()
        super(MinimalTestCase, self).tearDown()

    def prompt(self, message, question=None, message_type=None):
        """Prompt the user for a response.  Returns the users's input.

        This will block until the user responds.

        Sample usage::

             answer = self.prompt("What's the meaning of life?")
             assert answer == "42"

        :param message: The question to ask or message to give the
            user.

        :returns: The input from the user as a string.

        """

        response = None
        if not question:
            question = "Were you successful?"
        if not message_type:
            message_type = "PROMPT"

        print("\n\n=== %s ===\n%s" % (message_type, message))
        try:
            while response not in ["y", "n", ""]:
                response = raw_input("%s [Yn] " % question).lower()
        except (KeyboardInterrupt, EOFError):
            self.fail("Test interrupted by user")

        return response

    def instruct(self, message):
        """Instruct the user to do an action, such as rotating the phone.

        Sample usage::

            self.instruct("Rotate the phone 90 degrees")
            assert phone_rotation_changed()

        If the user informs us she failed to perform the instruction,
        the test will be failed.

        :param message: The instruction you want to give the user.

        """

        response = self.prompt(message, message_type="INSTRUCTION")
        if response == "n":
            self.fail("Failed on instruction: %s" % message)

    def confirm(self, message):
        """Ask the user to confirm a physical aspect about the device or the
        testing environment that cannot be checked by the test.

        An example of this would be the phone vibrating::

            vibrate()
            did_vibrate = yield self.confirm("Did you feel a vibration?")
            assert did_vibrate

        If the result of the confirmation is negative (false, no) the
        test will be failed.

        :param message: The confirmation to send to the user.

        """

        response = self.prompt(
            message, question="Response: ", message_type="CONFIRMATION")
        if response == "n":
            self.fail("Failed to confirm: %s" % message)

    def unplug_and_instruct(self, message):
        self.instruct(
            "Unplug the phone.\n%s\nPlug the phone back in after you are "
            "done, and unlock the screen if necessary.\n" % message)
        dm = mozdevice.DeviceManagerADB()
        dm.forward("tcp:2828", "tcp:2828")
        self.marionette = Marionette()
        self.marionette.start_session()
        self.use_cert_app()
