# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozdevice import DeviceManagerADB
from marionette import Marionette

class DeviceHelper(object):
    device = None
    marionette = None

    @staticmethod
    def getDevice(DeviceManager=DeviceManagerADB, **kwargs):
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
