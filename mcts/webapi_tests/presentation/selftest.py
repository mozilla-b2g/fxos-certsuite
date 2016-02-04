# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import moznetwork
import random
import re

from time import sleep
from adb_helper import AdbHelper
from mcts_apps import MCTSApps
from mdsn import ServiceListener
from presentation_controller.controller import PresentationApiController
from zeroconf import ServiceBrowser, Zeroconf

# Don't need to initial marionette in real test cases
from marionette import Marionette
m = Marionette('localhost', port=2828)
m.start_session()

# TODO: do it in different way for TV
# Get device IP for mDNS matching
device_ip = AdbHelper.adb_shell("ifconfig wlan0").split(" ")[2]
device_ip_webapi = m.execute_script("return navigator.mozWifiManager.connectionInformation.ipAddress;")

ip_reg = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
# TODO: Check ip_reg.match(device_ip)

# Initial socket client for testig purpose
controller_host = moznetwork.get_ip()
controller = PresentationApiController(host=controller_host)
controller_port = controller.get_port()

zeroconf = Zeroconf()
flag = False
listener = ServiceListener()

# Using MCTS apps for launching the app
mcts = MCTSApps(m)
manifesturl = mcts.getManifestURL(name="mctsapp")

print("MCTS Presentation APP manifestURL got.")

# Start [mDNS Services Discovery]
# Listen to _mozilla_papi._tcp in local area
browser = ServiceBrowser(zeroconf, "_mozilla_papi._tcp.local.", listener)

# Keep waiting for mDNS response till device found (30 seconds)
try:
    time = 30
    while (not flag) and time >= 0:
        sleep(0.2)
        flag = listener.check_ip(device_ip)
        time = time - 0.2
finally:
    zeroconf.close()

# TODO: Check ip_reg.match(flag[0])

print("Presentation API Server found - " + flag[0] + ":" + str(flag[1]))

# Start [Client - Target Device Communication]
# Setup presentation server's host and port
controller.set_pre_action(flag[0], flag[1])

# Send message to presentation server
msg_first = '{"type":"requestSession:Init", "id":"MCTS' + str(random.randint(1, 1000)) + '", "url":"' + manifesturl.replace("manifest.webapp", "index.html") + '", "presentationId":"presentationMCTS' + str(random.randint(1, 1000)) + '"}\n'
msg_second = '{"type":"requestSession:Offer", "offer":{"type":1, "tcpAddress":["' + controller_host + '"], "tcpPort":' + str(controller_port) + '}}\n'
controller.send_pre_action_message(msg_first + msg_second)
print(msg_first)
print(msg_second)

# Receive the message from presentation sever
pre_received = controller.recv_pre_action_message()

response = json.loads(pre_received.rstrip())
#TODO: Verify Controller Side Data: response["type"] == "requestSession:Answer"

# close socket
controller.finish_pre_action()

print(" " + pre_received.rstrip())
print("First phrase of presentation API communication done.")

# Start [Client Side Server - Target Device Communication]
# Start to accept
controller.start()

# Client side server sends message to target device
msg = 'echo'
controller.sendall(msg)
print('Send: {}'.format(msg))

#TODO: App Side Verification Required

# Client side server receives data/response
controller_received = controller.recv(1024)
print('Recv: {}'.format(controller_received))

print("Second phrase of presentation API communication done.")

#TODO: App Side Verification Required
