# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mcts.utils.handlers.adb_b2g import ADBB2G
from marionette import Marionette


class NoADB():
    def reboot(self):
        pass
    def wait_for_net(self):
        pass
    def shell_output(self):
        pass
    def forward(self, *args):
        pass
    def get_process_list(self):
        return [[1447, '/sbin/adbd', 'root']]
    def restart(self):
        pass
    def root(self):
        pass
    def devices(self, timeout=None):
        pass

class DeviceHelper(object):
    device = None
    marionette = None

    @staticmethod
    def getDevice(DeviceManager=ADBB2G, **kwargs):
        DeviceHelper.device = NoADB()
        if not DeviceHelper.device:
            DeviceHelper.device = DeviceManager(**kwargs)
            
            # forward only once after creating the device manager object
            hasadb = kwargs.pop('hasadb', True)
            if hasadb:
                DeviceHelper.device.forward("tcp:2828", "tcp:2828")

        return DeviceHelper.device
    
    @staticmethod
    def getMarionette(host='localhost', port=2828):
        if not DeviceHelper.marionette:
            DeviceHelper.marionette = Marionette(host, port)
            
        return DeviceHelper.marionette
