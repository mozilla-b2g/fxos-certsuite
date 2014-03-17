# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import SocketServer
import socket
import threading

import moznetwork

from webapi_tests import MinimalTestCase


"""Tests for the TCP Socket API available to privileged and certified
Firefox OS apps.

The TCPSocket API offers a whole API to open and use a TCP
connection. This allows app makers to implement any protocol available
on top of TCP such as IMAP, IRC, POP, HTTP, etc., or even build their
own to sustain any specific needs they could have.

Specification: https://developer.mozilla.org/en-US/docs/WebAPI/TCP_Socket

This test case is minimal and not exhaustive!

"""


class TCPServerHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print data
        self.request.sendall(data.upper())


class TCPTestServer(object):
    def __init__(self, addr, server_cls=None, handler_cls=None):
        self.addr = addr
        self.started = False

        if not server_cls:
            server_cls = SocketServer.TCPServer
        if not handler_cls:
            handler_cls = TCPServerHandler

        self.server = server_cls(self.addr, handler_cls)

    def start(self, block=False):
        """Start the socket server.

        :param block: True to run the server on the current thread,
            blocking, False to run on a separate thread.

        """

        self.started = True

        if block:
            self.server.start()
        else:
            self.server_thread = threading.Thread(
                target=self.server.serve_forever)
            self.server_thread.daemon = True  # don't hang on exit
            self.server_thread.start()

    def stop(self):
        """Stop the socket server.

        If the server is not running, this method has no effect.

        """

        if self.started:
            try:
                self.server.stop()
                self.server_thread.join()
                self.server_thread = None
            except AttributeError:
                pass
            self.started = False
        self.server = None

    def is_alive(self):
        """Ascertains whether the socket server has been started."""
        return self.started


def get_free_port(device="127.0.0.1"):
    """Retreives a free port in the ephermal range."""

    port = None
    so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        so.bind((device, 0))
        so.listen(3)
        port = so.getsockname()[1]
    finally:
        so.close()
    return port


class TcpSocketTestCase(MinimalTestCase):
    def setUp(self):
        super(TcpSocketTestCase, self).setUp()
        self.server = TCPTestServer((moznetwork.get_ip(), get_free_port()))
        self.server.start()

    def tearDown(self):
        self.server.stop()
        super(TcpSocketTestCase, self).tearDown()


class TestTcpSocketFormality(MinimalTestCase):
    def prop(self, pp, obj):
        return self.marionette.execute_script("return %s.%s" % (pp, obj))

    def prop_in(self, pp, obj):
        return self.marionette.execute_script("return '%s' in %s" % (pp, obj))

    def assert_property_in(self, pp, obj):
        is_present = self.prop_in(pp, obj)
        self.assertTrue(is_present, "%s property not found on %s" % (pp, obj))

    def test_api_available(self):
        self.assert_property_in("mozTCPSocket", "navigator")

    def test_properties(self):
        for prop in ["host", "port", "ssl", "bufferedAmount",
                     "binaryType", "readyState"]:
            self.assert_property_in(prop, "navigator.mozTCPSocket")

        self.assertEqual(self.prop("navigator.mozTCPSocket", "host"), "")
        self.assertEqual(self.prop("navigator.mozTCPSocket", "port"), 0)
        self.assertEqual(self.prop("navigator.mozTCPSocket", "ssl"), False)
        self.assertEqual(
            self.prop("navigator.mozTCPSocket", "readyState"), "closed")
        self.assertEqual(
            self.prop("navigator.mozTCPSocket", "binaryType"), "string")

        # The following code is preferable, but triggers a null
        # pointer exception in the bufferedAmount property function in
        # dom/network/TCPSocket.js.

        # props = self.marionette.execute_script(
        #     "return navigator.mozTCPSocket")
        # self.assertIn("host", props)
        # self.assertIn("port", props)
        # self.assertIn("ssl", props)
        # self.assertIn("bufferedAmount", props)
        # self.assertIn("binaryType", props)
        # self.assertIn("readyState", props)

        # self.assertEqual(props["host"], "")
        # self.assertEqual(props["port"], 0)
        # self.assertEqual(props["ssl"], False)
        # self.assertEqual(props["bufferedAmount"], 0)
        # self.assertEqual(props["readyState"], "closed")
        # self.assertEqual(props["binaryType"], "string")


# class TestTcpSocketOpen(TcpSocketTestCase):
    # def test_connect_fail(self):
    #     pass

    # def test_connect(self):
    #     pass

    # def test_connect_with_binarytype_arraybuffer(self):
    #     self.marionette.execute_script(
    #         "let so = navigator.mozTCPSocket.open('%s', %d, "
    #         "{'binaryType': 'arraybuffer'})" %
    #         (self.server.addr[0], self.server.addr[1]))
    #     self.assertEqual(self.marionette.execute_script("return so.binaryType",
    #                                                     "arraybuffer"))

    # def test_close(self):
    #     pass

    # def test_upgrade_to_secure(self):
    #     pass

    # TODO(ato): Add SSL tests


# class TestTcpSocketTransmit(TcpSocketTestCase):
#     def test_send_string(self):
#         pass

#     def test_send_uint8array(self):
#         pass

#     def test_send_no_data(self):
#         pass

#     def test_send_128kb_data_returns_false(self):
#         pass

#     def test_send_128kb_data_triggers_ondrain(self):
#         pass


# class TestTcpSocketReceive(TcpSocketTestCase):
#     def test_buffered_amount(self):
#         pass

#     def test_receives_string_data(self):
#         pass

#     def test_receives_arraybuffer_data(self):
#         pass

#     def test_suspend_stops_firing_ondata(self):
#         pass

#     def test_resume_starts_firing_ondata(self):
#         pass


# class TestTcpSocketEvents(TcpSocketTestCase):
#     def test_onopen(self):
#         pass

#     def test_ondrain(self):
#         pass

#     def test_ondata(self):
#         pass

#     def test_onerror(self):
#         pass

#     def test_onclose(self):
#         pass


# class TestTcpServerSocket(MinimalTestCase):
#     def test_listen_on_port_below_1024(self):
#         pass

#     def test_listen_on_port_above_1024(self):
#         pass

#     # TODO(ato): Tests missing here
