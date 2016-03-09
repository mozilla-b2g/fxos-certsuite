# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

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
        # self.wait_for_obj("window.navigator.presentation")

        # Initial socket server for testig purpose
        self.controller = PresentationApiController()
        self.controller_host = self.controller.get_addr()
        self.controller_port = self.controller.get_port()

    def test_full_presentation_flow(self):
        zeroconf = Zeroconf()
        flag = False
        listener = ServiceListener()

        # Get device IP for mDNS matching
        self.device_ip = self.prompt("Please enter ip of TV in aaa.bbb.xxx.yyy format")

        # Start [mDNS Services Discovery]
        # Listen to _mozilla_papi._tcp in local area
        browser = ServiceBrowser(zeroconf, "_mozilla_papi._tcp.local.", listener)

        # Keep waiting for mDNS response till device found (30 seconds)
        try:
            t = 30
            while (not flag) and t >= 0:
                time.sleep(0.2)
                flag = listener.check_ip(self.device_ip)
                t = t - 0.2
        finally:
            zeroconf.close()

        # Start [Client - Target Device Communication]
        # Setup presentation server's host and port
        self.controller.set_pre_action(flag[0], flag[1])

        # Send message to presentation server
        rand_int = str(random.randint(1, 1000))
        msg_first = '{"type":"requestSession:Init", "id":"MCTS' + rand_int + '", "url":"app://notification-receiver.gaiamobile.org/index.html", "presentationId":"presentationMCTS' + rand_int + '"}\n'
        msg_second = '{"type":"requestSession:Offer", "offer":{"type":1, "tcpAddress":["' + self.controller_host + '"], "tcpPort":' + str(self.controller_port) + '}}\n'
        self.controller.send_pre_action_message(msg_first + msg_second)

        # Receive the message from presentation sever
        pre_received = self.controller.recv_pre_action_message()
        response = json.loads(pre_received.rstrip())

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

        self.assertTrue((self.controller_received != ""), "Expected to receive messages.")

    def clean_up(self):
        # shut down all services
        pass

