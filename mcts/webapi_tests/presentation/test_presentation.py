# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from adb_helper import AdbHelper
from mcts_apps import MCTSApps
from mdsn import ServiceListener
from presentation_controller.controller import PresentationApiController
from zeroconf import ServiceBrowser, Zeroconf
from mcts.webapi_tests.semiauto import TestCase


class TestPresentation(TestCase):
    """
    This is a test for the `Presentation API`_ which will:

    - Test TCP transport channel (Init, Offer, and Answer)
    - Verify if TCP communication is valid
    - Verify basic webapi works

    """

    def setUp(self):
        super(TestPresentation, self).setUp()
        self.wait_for_obj("window.navigator.presentation")

        # TODO: Get device IP for mDNS matching
        self.device_ip = AdbHelper.adb_shell("ifconfig wlan0").split(" ")[2]

        # Initial socket server for testig purpose
        self.controller = PresentationApiController()
        self.controller_host = controller.get_addr()
        self.controller_port = controller.get_port()

    def test_full_presentation_flow(self):
        zeroconf = Zeroconf()
        flag = False
        listener = ServiceListener()

        # Using MCTS apps for launching the app
        mcts = MCTSApps(self.marionette)
        manifesturl = mcts.getManifestURL(name="mctsapp")
        mcts.launch("MCTS")

        # TODO: need to find the manifest url for MCTS presentation api test app
        #       should parse this information to Socket Client for json to be sent

        # Start [mDNS Services Discovery]
        # Listen to _mozilla_papi._tcp in local area
        browser = ServiceBrowser(zeroconf, "_mozilla_papi._tcp.local.", listener)

        # Keep waiting for mDNS response till device found (30 seconds)
        try:
            time = 30
            while (not flag) and time >= 0:
                sleep(0.2)
                flag = listener.check_ip(self.device_ip)
                time = time - 0.2
        finally:
            zeroconf.close()

        # Start [Client - Target Device Communication]
        # Setup presentation server's host and port
        self.controller.set_pre_action(flag[0], flag[1])

        # Send message to presentation server
        msg_first = '{"type":"requestSession:Init", "id":"MCTS", "url":"app://notification-receiver.gaiamobile.org/index.html", "presentationId":"presentationMCTS"}'
        msg_second = '{"type":"requestSession:Offer", "offer":{"type":1, "tcpAddress":["' + self.controller_host + '"], "tcpPort":' + str(self.controller_port) + '}}'
        self.controller.send_pre_action_message(msg_first)
        self.controller.send_pre_action_message(msg_second)

        # Receive the message from presentation sever
        pre_received = self.controller.recv_pre_action_message()

        # close socket
        self.controller.finish_pre_action()

        # Start [Client Side Server - Target Device Communication]
        # Start listen
        self.controller.start()

        # Client side server sends message to target device
        msg = 'This is Controller\'s first message.'
        self.controller.sendall(msg)
        print('Send: {}'.format(msg))

        # Client side server receives data/response
        self.controller_received = self.controller.recv(1024)
        print('Recv: {}'.format(self.controller_received))

        self.assertTrue((self.controller_received != ""), "Expected message returned.")

    def clean_up(self):
        # shut down all services
        pass

